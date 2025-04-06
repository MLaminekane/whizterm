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
import io 
import threading 
import customtkinter 
from typing import Optional, List 

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
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
        # Si c'est une désinstallation on vérifie d'abord si l'application est installée
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
        # prompt système
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
        self.text_widget.after(0, self._write_to_widget, string)

    def _write_to_widget(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("WhizTerm")
        self.geometry("800x600")
        
        # thème sombre
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        
        # couleur de fond en noir
        self.configure(fg_color="black")

        self.current_directory = os.getcwd()

        # Ajouter le chemin de Homebrew au PATH
        homebrew_path = "/opt/homebrew/bin"
        if os.path.exists(homebrew_path):
            os.environ["PATH"] = f"{homebrew_path}:{os.environ['PATH']}"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        # Frame pour la zone de saisie en haut
        self.input_frame = customtkinter.CTkFrame(self, fg_color="black", corner_radius=0)
        self.input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Prompt du terminal 
        self.prompt_label = customtkinter.CTkLabel(
            self.input_frame,
            text="$ ",
            text_color="lime green",
            font=("Courier", 14)
        )
        self.prompt_label.grid(row=0, column=0, padx=(5, 0))

        # Champ de saisie pour les commandes (en haut)
        self.input_entry = customtkinter.CTkEntry(
            self.input_frame,
            placeholder_text="run commands...",
            border_width=0,
            fg_color="black",
            text_color="white",
            font=("Courier", 14)
        )
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.input_entry.bind("<Return>", self.process_gui_command)

        # Zone de texte pour la sortie 
        self.output_textbox = customtkinter.CTkTextbox(
            self,
            state="disabled",
            wrap="word",
            fg_color="black",
            text_color="white",
            font=("Courier", 12)
        )
        self.output_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Redirection stdout/stderr
        self.redirector = OutputRedirector(self.output_textbox)
        sys.stdout = self.redirector
        sys.stderr = self.redirector
        
        # Message de bienvenue
        # print("[bold cyan]Bienvenue dans WhizTerm.[/bold cyan]")

    def update_prompt(self):
        """Met à jour le prompt avec le répertoire courant"""
        current_dir = os.path.basename(self.current_directory) or '/'
        self.prompt_label.configure(text=f"{current_dir} $ ")

    def execute_shell_command(self, command: str):
        """
        Exécute une commande shell en tenant compte du répertoire courant
        """
        try:
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
                    self.update_prompt()  # Mettre à jour le prompt
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
        """Traite la commande entrée dans l'interface graphique"""
        command = self.input_entry.get().strip()
        if not command:
            return

        # Effacer le champ de saisie
        self.input_entry.delete(0, "end")

        # Afficher la commande entrée
        print(f"> {command}")

        try:
            # Vérifier si c'est une salutation
            if self.is_greeting(command):
                print(f"AI: {self.get_greeting_response(command)}")
                return

            # Vérifier si c'est une commande shell directe
            if self.is_shell_command(command):
                self.execute_shell_command(command)
                return

            # Sinon, traiter comme une requête à l'IA
            response = self.ask_ai(command)
            
            # Extraire et exécuter les commandes de la réponse
            commands = self.extract_commands(response)
            if commands:
                for cmd in commands:
                    self.execute_command(cmd)
            else:
                # Si pas de commande, afficher juste la réponse de l'IA
                print(f"AI: {response}")

        except Exception as e:
            print(f"Erreur: {str(e)}")

    def execute_command(self, command: str):
        """Exécute une commande et affiche le résultat"""
        try:
            # Nettoyer la commande des backticks
            command = command.strip('`')
            
            # Vérifier si la commande nécessite des droits administrateur
            if any(cmd in command.lower() for cmd in ['sudo', 'brew']):
                command = command.replace('sudo ', '')
            
            # Exécuter la commande
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Afficher le résultat
            if result.stdout:
                print(result.stdout.rstrip())
            if result.stderr:
                print(f"Erreur: {result.stderr.rstrip()}")
            elif not result.stdout and not result.stderr:
                print("Succès")

        except Exception as e:
            print(f"Erreur: {str(e)}")

    def is_shell_command(self, command: str) -> bool:
        """
        Vérifie si la commande est une commande shell directe
        """
        shell_commands = {'ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'echo', 'grep'}
        first_word = command.strip().split()[0]
        return first_word in shell_commands or '/' in command or '.' in command

    def ask_ai(self, prompt: str) -> str:
        """Envoie une requête à l'API Ollama et retourne la réponse"""
        try:
            system_prompt = """Tu es un assistant concis pour macOS.
            - Réponds en une seule phrase courte
            - Pour installer des applications sur macOS, utilise uniquement 'brew install --cask'
            - Pour désinstaller des applications sur macOS, utilise uniquement 'brew uninstall --cask'
            - N'utilise jamais apt, apt-get ou d'autres gestionnaires Linux
            - Mets les commandes entre ```
            - Pas d'explications, juste la commande
            -Pas d'explications supplémentaires ni de texte qui n'est pas demande 
            - Si c'est une salutation, réponds simplement le plus court possible
            - Si c'est une question, donne une réponse directe rien de plus
            - Si c'est une demande de commande, donne uniquement la commande entre ```
            - Pas de traduction ou d'explications linguistiques repond le plus petit possible"""

            data = {
                "model": "mistral",
                "prompt": f"{system_prompt}\n\nUtilisateur: {prompt}",
                "stream": False
            }
            
            response = requests.post(OLLAMA_API_URL, json=data)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            return "Erreur: Ollama n'est pas en cours d'exécution"
        except Exception as e:
            return f"Erreur: {str(e)}"

    def extract_commands(self, text: str) -> List[str]:
        """Extrait les commandes du texte généré par l'IA"""
        commands = re.findall(r'```(.*?)```', text, re.DOTALL)
        if not commands:
            commands = re.findall(r'`(.*?)`', text)
        return [cmd.strip() for cmd in commands if cmd.strip()]

    def is_greeting(self, text: str) -> bool:
        """Vérifie si le texte est une salutation simple"""
        greetings = {
            'salut', 'bonjour', 'hello', 'hi', 'hey', 'coucou',
            'bonsoir', 'yo', 'hola', 'ola'
        }
        return text.lower().strip() in greetings

    def get_greeting_response(self, text: str) -> str:
        """Retourne une réponse simple pour les salutations"""
        return "Salut ! Comment puis-je vous aider ?"

# def interactive_mode():
#     print("[bold cyan]Bienvenue dans le mode interactif de WhizTerm.[/bold cyan]")
#     print("Entrez 'quitter' pour sortir.")
#     while True:
#         command_input = input("> ")
#         if command_input.lower() == 'quitter':
#             break
#         try:
#             if command_input.strip():
#                 parts = command_input.split(maxsplit=1)
#                 cmd_name = parts[0]
#                 args = parts[1] if len(parts) > 1 else ""
#                 typer_command = None
#                 for command_info in app.registered_commands:
#                     if command_info.name == cmd_name:
#                         typer_command = command_info.callback
#                         break
                
#                 if typer_command:
#                     if cmd_name == 'process-command':
#                         process_command(command=args, model="mistral") 
#                     elif cmd_name == 'search-files':
#                         search_files(query=args)
#                     elif cmd_name == 'list-models':
#                         list_models()
#                     else:
#                         print(f"[bold red]Commande Typer non gérée en mode interactif: {cmd_name}[/bold red]")
#                 else:
#                     process_command(command=command_input, model="mistral")
            
#         except Exception as e:
#             print(f"[bold red]Erreur en mode interactif:[/bold red] {str(e)}")

if __name__ == "__main__":
    gui_app = App()
    gui_app.mainloop()
    
