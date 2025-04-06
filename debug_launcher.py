#!/usr/bin/env python3
"""
Script de lancement avec débogage pour WhizTerm
Ce script lance l'application et capture toutes les erreurs
"""
import os
import sys
import traceback
import tempfile
import datetime

# Créer un fichier de log pour capturer les erreurs
log_path = os.path.join(tempfile.gettempdir(), "whizterm_debug.log")

try:
    with open(log_path, "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n--- Démarrage WhizTerm {timestamp} ---\n")
        log_file.write(f"Répertoire de travail: {os.getcwd()}\n")
        log_file.write(f"Python: {sys.version}\n")
        log_file.write(f"Chemin système: {sys.path}\n")
        log_file.write(f"Arguments: {sys.argv}\n")

    # Ici, importez et lancez votre application principale
    from whizterm import app
    
    # Si l'application utilise typer
    if __name__ == "__main__":
        if len(sys.argv) <= 1:
            # Mode interactif
            from whizterm import interactive_mode
            interactive_mode()
        else:
            # Mode commande
            app()
            
except Exception as e:
    # Capturer et enregistrer toutes les erreurs
    with open(log_path, "a") as log_file:
        log_file.write(f"\nERREUR: {str(e)}\n")
        log_file.write(traceback.format_exc())
        log_file.write("\n--- Fin du journal d'erreurs ---\n")

    print(f"Une erreur s'est produite: {str(e)}")
    print(f"Détails de l'erreur enregistrés dans: {log_path}")
    
   
    sys.exit(1)
