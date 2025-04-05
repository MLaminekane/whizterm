import PyInstaller.__main__

def create_executable():
    """
    Crée un exécutable de l'application avec PyInstaller
    """
    PyInstaller.__main__.run([
        '--name=WhizTerm',
        '--onefile',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build',
        '--add-data=assets;assets',
        '--add-data=locales;locales',
        '--add-data=templates;templates',
        '--add-data=whizterm.py;.',
        '--add-data=README.md;.',
        '--add-data=LICENSE;.',
        '--add-data=CHANGELOG.md;.',
        '--add-data=VERSION;.',
        '--add-data=whizterm.spec;.',
        '--windowed',
        '--add-data=requirements.txt;.',
        '--icon=assets/icon.ico',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    create_executable()
