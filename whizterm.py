import typer
from rich import print
from rich.syntax import Syntax
from rich.panel import Panel
import requests
from dotenv import load_dotenv
import os
import subprocess
import shlex
import re
import pathlib
import logging
import sys
import io # Added for redirecting stdout/stderr
import threading # Added for running commands in background
import customtkinter # Added for GUI
from typing import Optional, List # Added for type hints

# --- Début des modifications pour PyInstaller ---
def get_base_path():
    # Détermine le chemin de base pour les ressources
    if getattr(sys, 'frozen', False):
        # Si l'application est "gelée" (exécutée via PyInstaller)
        return sys._MEIPASS
    else:
        # Sinon (exécutée comme un script normal)
        return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()
dotenv_path = os.path.join(base_path, '.env')

# Afficher les informations de débogage
print(f"[DEBUG] Répertoire de travail actuel (CWD): {os.getcwd()}")
print(f"[DEBUG] Chemin de base détecté: {base_path}")
print(f"[DEBUG] Tentative de chargement de .env depuis: {dotenv_path}")

# Charger .env depuis le chemin correct
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print("[DEBUG] Fichier .env chargé.")
else:
    print("[DEBUG] Fichier .env non trouvé au chemin attendu.")
# --- Fin des modifications pour PyInstaller ---

app = typer.Typer()

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def call_ollama_api(prompt: str, model: str = "mistral"):
    """
    Appelle l'API Ollama
    """
    try:
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(OLLAMA_API_URL, json=data)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        return "Erreur: Impossible de se connecter à Ollama. Assurez-vous qu'Ollama est en cours d'exécution."
    except Exception as e:
        return f"Erreur lors de l'appel à Ollama: {str(e)}"

def extract_commands(text: str):
    """
    Extrait les commandes du texte généré par l'IA
    """
    # Recherche les commandes entre backticks
    commands = re.findall(r'```(.*?)```', text, re.DOTALL)
    if not commands:
        commands = re.findall(r'`(.*?)`', text)
    # Nettoyer les commandes
    return [cmd.strip() for cmd in commands if cmd.strip()]

def execute_command(command: str):
    """
    Exécute une commande système
    """
    try:
        # Nettoyer la commande des backticks
        command = command.strip('`')
        
        # Vérifier si la commande nécessite des droits d'administration
        if any(cmd in command.lower() for cmd in ['apt install', 'dnf install', 'yum install']):
            command = f"sudo {command}"
        # Ne pas utiliser sudo avec brew
        elif 'brew install' in command.lower():
            command = command.replace('sudo ', '')
            
        print(f"[bold yellow]Exécution de la commande:[/bold yellow] {command}")
        
        # Exécuter la commande et capturer la sortie
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Afficher la sortie
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"[bold red]Erreur:[/bold red] {result.stderr}")
        
        if result.returncode == 0:
            return "Commande exécutée avec succès"
        else:
            return f"Erreur lors de l'exécution de la commande (code: {result.returncode})"
            
    except Exception as e:
        return f"Erreur lors de l'exécution de la commande: {str(e)}"

def find_cask_name(app_name: str, is_uninstall: bool = False) -> str:
    """
    Trouve le nom exact du cask pour une application
    """
    try:
        # Si c'est une désinstallation, vérifier d'abord si l'application est installée
        if is_uninstall:
            check_cmd = f"brew list --cask | grep -i {app_name}"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return app_name  # Si l'application est installée, utiliser le nom tel quel
        
        # Rechercher dans les casks Homebrew
        search_cmd = f"brew search {app_name}"
        result = subprocess.run(search_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Analyser la sortie pour trouver le bon cask
            lines = result.stdout.split('\n')
            for line in lines:
                if 'cask' in line.lower():
                    # Extraire le nom du cask
                    cask_name = line.split('/')[-1].strip()
                    return cask_name
        
        # Si pas trouvé, essayer une recherche plus large
        search_cmd = f"brew search --desc {app_name}"
        result = subprocess.run(search_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'cask' in line.lower():
                    cask_name = line.split('/')[-1].strip()
                    return cask_name
        
        return app_name  # Retourner le nom original si pas trouvé
    except Exception as e:
        print(f"Erreur lors de la recherche du cask: {str(e)}")
        return app_name

def find_installed_app(app_name: str) -> str:
    """
    Trouve une application installée dans le système
    """
    try:
        # Chercher dans /Applications
        find_cmd = f"find /Applications -name '*{app_name}*' -type d -maxdepth 1"
        result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            app_path = result.stdout.strip()
            app_name = os.path.basename(app_path)
            return app_name.replace('.app', '')
        
        # Chercher avec mdfind (Spotlight)
        find_cmd = f"mdfind 'kMDItemKind==Application' | grep -i {app_name}"
        result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            app_path = result.stdout.strip().split('\n')[0]
            app_name = os.path.basename(app_path)
            return app_name.replace('.app', '')
        
        return app_name
    except Exception as e:
        print(f"Erreur lors de la recherche de l'application: {str(e)}")
        return app_name

def uninstall_app(app_name: str) -> str:
    """
    Désinstalle une application
    """
    try:
        # Essayer d'abord avec Homebrew
        brew_cmd = f"brew uninstall --cask {app_name}"
        result = subprocess.run(brew_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Application désinstallée avec Homebrew: {result.stdout}"
        
        # Si Homebrew échoue, essayer de supprimer manuellement avec sudo
        app_path = f"/Applications/{app_name}.app"
        if os.path.exists(app_path):
            rm_cmd = f"sudo rm -rf '{app_path}'"
            result = subprocess.run(rm_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return "Application désinstallée manuellement"
            else:
                return f"Erreur lors de la désinstallation manuelle: {result.stderr}"
        
        return "Application non trouvée"
    except Exception as e:
        return f"Erreur lors de la désinstallation: {str(e)}"

@app.command()
def process_command(
    command: str, 
    model: str = typer.Option("mistral", "--model", "-m", help="Modèle Ollama à utiliser"),
    auto_execute: bool = typer.Option(True, "--execute", "-e", help="Exécuter automatiquement les commandes suggérées")
):
    """
    Traite les commandes utilisateur avec l'IA Ollama
    """
    try:
        # Préparation du prompt système
        system_prompt = """Tu es un assistant terminal AI qui aide à exécuter des commandes et gérer des fichiers.
        Tu peux aider à :
        - Rechercher des fichiers
        - Exécuter des commandes système
        - Créer ou modifier des fichiers
        - Installer des applications
        
        IMPORTANT : 
        - Réponds de manière concise et directe
        - Pour toute commande système à exécuter, place-la entre triple backticks (```)
        - Ne demande pas de confirmation à l'utilisateur
        - Exécute directement les commandes nécessaires pour accomplir la tâche demandée
        - Ne mets pas de texte avant ou après les backticks de la commande
        - Pour les installations sur macOS, utilise toujours brew
        - Pour les applications GUI sur macOS, utilise toujours brew --cask
        - Pour désinstaller une application, utilise toujours la commande appropriée
        - Si l'installation nécessite des étapes supplémentaires, indique-les clairement"""
        
        full_prompt = f"{system_prompt}\n\nCommande utilisateur: {command}"
        
        # Appel à l'API Ollama
        ai_response = call_ollama_api(full_prompt, model)
        print(f"[bold green]AI:[/bold green] {ai_response}")
        
        # Extraire et exécuter les commandes
        commands = extract_commands(ai_response)
        if commands:
            print("\n[bold yellow]Commandes extraites:[/bold yellow]")
            for cmd in commands:
                # Si c'est une commande de désinstallation, trouver l'application
                if 'uninstall' in cmd.lower():
                    app_name = cmd.split()[-1]
                    installed_app = find_installed_app(app_name)
                    if installed_app != app_name:
                        print(f"[bold yellow]Application trouvée:[/bold yellow] {installed_app}")
                        result = uninstall_app(installed_app)
                        print(result)
                    else:
                        print(f"[bold red]Application non trouvée:[/bold red] {app_name}")
                else:
                    print(f"[bold blue]Exécution de:[/bold blue] {cmd}")
                    result = execute_command(cmd)
                    print(result)
        else:
            print("\n[bold yellow]Aucune commande trouvée dans la réponse.[/bold yellow]")
        
    except Exception as e:
        print(f"[bold red]Erreur:[/bold red] {str(e)}")

@app.command()
def search_files(query: str):
    """
    Recherche des fichiers dans le système
    """
    results = Path().rglob(f"*{query}*")
    for result in results:
        print(f"[blue]{result}[/blue]")

@app.command()
def list_models():
    """
    Liste les modèles Ollama disponibles
    """
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        models = response.json()["models"]
        print("[bold green]Modèles disponibles:[/bold green]")
        for model in models:
            print(f"- {model['name']}")
    except requests.exceptions.ConnectionError:
        print("[bold red]Erreur: Impossible de se connecter à Ollama. Assurez-vous qu'Ollama est en cours d'exécution.[/bold red]")
    except Exception as e:
        print(f"[bold red]Erreur:[/bold red] {str(e)}")

# --- Classes for GUI ---

class OutputRedirector(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, string):
        # Assurez-vous que les mises à jour du widget se font dans le thread principal
        self.text_widget.after(0, self._write_to_widget, string)

    def _write_to_widget(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        # Tkinter Text widget n'a pas besoin de flush explicite
        pass

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("WhizTerm")
        self.geometry("800x600")
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        # Garder une trace du répertoire de travail courant
        self.current_directory = os.getcwd()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Zone de texte pour la sortie
        self.output_textbox = customtkinter.CTkTextbox(self, state="disabled", wrap="word")
        self.output_textbox.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        # Champ de saisie pour les commandes
        self.input_entry = customtkinter.CTkEntry(self, placeholder_text="Entrez votre commande ici...")
        self.input_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.input_entry.bind("<Return>", self.process_gui_command)

        # Redirection stdout/stderr
        self.redirector = OutputRedirector(self.output_textbox)
        sys.stdout = self.redirector
        sys.stderr = self.redirector
        
        print("[bold cyan]Bienvenue dans WhizTerm.[/bold cyan]")
        print("Entrez votre commande ci-dessous et appuyez sur Entrée.")

    def is_shell_command(self, command: str) -> bool:
        """
        Vérifie si la commande est une commande shell directe
        """
        shell_commands = {'ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'echo', 'grep'}
        first_word = command.strip().split()[0]
        return first_word in shell_commands or '/' in command or '.' in command

    def execute_shell_command(self, command: str):
        """
        Exécute une commande shell en tenant compte du répertoire courant
        """
        try:
            # Gérer la commande cd séparément car elle affecte l'état
            if command.startswith('cd'):
                new_dir = command[2:].strip()
                if not new_dir:
                    new_dir = os.path.expanduser('~')
                
                # Gérer les chemins relatifs et absolus
                if not os.path.isabs(new_dir):
                    new_dir = os.path.join(self.current_directory, new_dir)
                
                # Vérifier si le répertoire existe
                if os.path.isdir(new_dir):
                    self.current_directory = os.path.abspath(new_dir)
                    os.chdir(self.current_directory)
                    print(f"Répertoire courant : {self.current_directory}")
                else:
                    print(f"Erreur : Le répertoire {new_dir} n'existe pas")
                return

            # Pour les autres commandes
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.current_directory
            )

            if result.stdout:
                print(result.stdout.rstrip())
            if result.stderr:
                print(f"Erreur : {result.stderr.rstrip()}")

        except Exception as e:
            print(f"Erreur lors de l'exécution de la commande : {str(e)}")

    def process_gui_command(self, event=None):
        command_input = self.input_entry.get()
        self.input_entry.delete(0, "end")  # Efface le champ après envoi
        print(f"> {command_input}")  # Affiche la commande entrée
        
        if command_input.lower() == 'quitter':
            self.quit()
            return

        # Vérifier si c'est une commande shell directe
        if self.is_shell_command(command_input):
            self.execute_shell_command(command_input)
        else:
            # Sinon, traiter comme une requête pour l'IA
            thread = threading.Thread(target=self.run_command_logic, args=(command_input,), daemon=True)
            thread.start()

    def run_command_logic(self, command_input):
        try:
            if command_input.strip():
                # Traiter comme une commande AI par défaut
                process_command(command=command_input, model="mistral")
        except Exception as e:
            print(f"[bold red]Erreur lors du traitement de la commande:[/bold red] {str(e)}")

def interactive_mode():
    # Cette fonction n'est plus utilisée pour l'application GUI principale
    print("[bold cyan]Bienvenue dans le mode interactif de WhizTerm.[/bold cyan]")
    print("Entrez 'quitter' pour sortir.")
    while True:
        command_input = input("> ")
        if command_input.lower() == 'quitter':
            break
        try:
            # Simuler l'appel Typer. On pourrait rendre ça plus robuste
            # mais pour un début, on assume que l'utilisateur entre 'process-command <sa commande>'
            # ou une autre commande valide de WhizTerm.
            # Attention: ne gère pas les options comme --model pour l'instant.
            if command_input.strip():
                # Diviser l'entrée en commande et arguments
                parts = command_input.split(maxsplit=1)
                cmd_name = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                
                # Trouver la fonction Typer correspondante
                typer_command = None
                for command_info in app.registered_commands:
                    if command_info.name == cmd_name:
                        typer_command = command_info.callback
                        break
                
                if typer_command:
                    # Ici, on appelle directement la fonction. 
                    # Pour process_command, il faut passer l'argument 'command'.
                    # Pour d'autres, il faut adapter.
                    if cmd_name == 'process-command':
                        process_command(command=args, model="mistral") 
                    elif cmd_name == 'search-files':
                        search_files(query=args)
                    elif cmd_name == 'list-models':
                        list_models()
                    else:
                        print(f"[bold red]Commande Typer non gérée en mode interactif: {cmd_name}[/bold red]")
                else:
                    # Si ce n'est pas une commande Typer, on tente de la traiter comme une commande AI
                    process_command(command=command_input, model="mistral")
            
        except Exception as e:
            print(f"[bold red]Erreur en mode interactif:[/bold red] {str(e)}")

if __name__ == "__main__":
    # Lancer l'application GUI
    gui_app = App()
    gui_app.mainloop()
    
    # L'ancien code pour Typer ou le mode interactif n'est plus utilisé ici
    # if len(sys.argv) <= 1:
    #     interactive_mode()
    # else:
    #     # Sinon, laisser Typer gérer les arguments comme d'habitude
    #     app()