# WhizTerm

WhizTerm est un assistant terminal intelligent qui vous aide à gérer votre système macOS avec des commandes naturelles. Il utilise l'IA pour comprendre vos demandes et exécuter les commandes appropriées.

## Fonctionnalités

- 🧠 Compréhension des commandes en langage naturel
- 📦 Gestion des applications (installation, désinstallation)
- 🔍 Recherche intelligente des applications
- 🚀 Exécution automatique des commandes
- 💻 Support complet de Homebrew
- 🛠️ Gestion des fichiers et dossiers
- 🔄 Support multilingue (français, anglais)

## Prérequis

- macOS
- Python 3.8+
- [Ollama](https://ollama.ai/) installé avec le modèle Mistral

## Installation

1. Clonez le dépôt :

```bash
git clone https://github.com/votre-username/whizterm.git
cd whizterm
```

2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

3. Assurez-vous qu'Ollama est en cours d'exécution :

```bash
ollama serve
```

## Utilisation

### Commandes de base

```bash
# Traiter une commande
python whizterm.py process-command "installer chrome"

# Utiliser un modèle spécifique
python whizterm.py process-command "desinstaller telegram" --model mistral

# Désactiver l'exécution automatique
python whizterm.py process-command "chercher un fichier" --execute false
```

### Exemples de commandes

- Installation d'applications :

  ```bash
  python whizterm.py process-command "installer visual studio code"
  ```

- Désinstallation d'applications :

  ```bash
  python whizterm.py process-command "desinstaller telegram"
  ```

- Recherche de fichiers :

  ```bash
  python whizterm.py process-command "chercher tous les fichiers pdf"
  ```

- Gestion de fichiers :
  ```bash
  python whizterm.py process-command "créer un dossier projet"
  ```

## Configuration

Vous pouvez configurer WhizTerm en modifiant les paramètres suivants :

- Modèle par défaut : `mistral`
- Langue par défaut : `fr`
- Exécution automatique : `true`

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur

Lamine Kane => DarkGunther

## Portfolio
darkgunther.ninja

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.
