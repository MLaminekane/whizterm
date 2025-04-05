import os
import shutil
import customtkinter
import sys

def copy_customtkinter_resources():
    # Get CustomTkinter package location
    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"CustomTkinter path: {ctk_path}")
    
    # Define source and destination paths
    assets_src = os.path.join(ctk_path, 'assets')
    assets_dest = os.path.join('dist', 'WhizTerm.app', 'Contents', 'MacOS', 'customtkinter', 'assets')
    
    print(f"Source path: {assets_src}")
    print(f"Destination path: {assets_dest}")
    
    # Create destination directory if it doesn't exist
    os.makedirs(assets_dest, exist_ok=True)
    
    # Copy assets
    if os.path.exists(assets_src):
        print("Copying assets...")
        for item in os.listdir(assets_src):
            s = os.path.join(assets_src, item)
            d = os.path.join(assets_dest, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print("Assets copied successfully!")
    else:
        print(f"Error: Assets directory not found at {assets_src}")
        sys.exit(1)

if __name__ == '__main__':
    copy_customtkinter_resources() 