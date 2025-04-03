import typer
from rich import print
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import json
import subprocess
import re

app = typer.Typer()
load_dotenv()


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

if __name__ == "__main__":
    app()