# setup.py
from setuptools import setup

APP = ['whizterm.py']
DATA_FILES = ['.env'] # Inclut le fichier .env à la racine de l'app bundle
OPTIONS = {
    'argv_emulation': True, # Permet le passage d'arguments si nécessaire
    # 'packages': ['requests', 'rich', 'typer', 'dotenv'], # Suppression pour laisser py2app gérer les dépendances
    'plist': {
        'CFBundleName': 'WhizTerm',
        'CFBundleDisplayName': 'WhizTerm',
        'CFBundleGetInfoString': "WhizTerm AI Terminal Assistant",
        'CFBundleIdentifier': "com.yourdomain.whizterm", # Remplacez par votre identifiant
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
        'NSHumanReadableCopyright': u"Copyright © 2024, Votre Nom ou Entreprise" # Mettez à jour le copyright
    },
    # 'iconfile': 'path/to/your/icon.icns', # Décommentez et modifiez si vous avez une icône
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 