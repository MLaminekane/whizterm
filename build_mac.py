import PyInstaller.__main__
import os
import sys

def create_mac_app():
    """
    Crée une application macOS avec PyInstaller
    """
    # Vérifier si les fichiers existent pour éviter les erreurs
    file_checks = {
        '.env': False,
        'whizterm.py': True,  # Fichier principal (obligatoire)
    }
    
    # Liste des fichiers à ajouter s'ils existent
    optional_files = [
        ('assets', 'assets'),
        ('locales', 'locales'),
        ('templates', 'templates'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('CHANGELOG.md', '.'),
        ('VERSION', '.'),
        ('requirements.txt', '.'),
        ('icon.icns', '.')  # Icône pour macOS (format .icns)
    ]
    
    # Vérifier les fichiers obligatoires
    for file, required in file_checks.items():
        if required and not os.path.exists(file):
            print(f"Erreur: Fichier requis '{file}' non trouvé.")
            sys.exit(1)
    
    # Préparer les datas avec la syntaxe macOS (: au lieu de ;)
    datas = []
    for file, dest in optional_files:
        if os.path.exists(file):
            datas.append(f'--add-data={file}:{dest}')
    
    # Toujours ajouter .env s'il existe
    if os.path.exists('.env'):
        datas.append('--add-data=.env:.')
    
    # Configuration de base
    command = [
        'whizterm.py',
        '--name=WhizTerm',
        '--onefile',
        '--windowed',  # Pour une application GUI
        '--clean',
        '--noconfirm',
        '--osx-bundle-identifier=com.darkgunther.whizterm',
    ]
    
    # Ajouter les hiddenimports
    command.extend([
        '--hidden-import=typer',
        '--hidden-import=rich',
        '--hidden-import=requests',
        '--hidden-import=python-dotenv',
    ])
    
    # Ajouter les fichiers de données
    command.extend(datas)
    
    # Exécuter PyInstaller
    print("Démarrage de la construction de l'application...")
    PyInstaller.__main__.run(command)
    print("Construction terminée.")

if __name__ == '__main__':
    create_mac_app()
