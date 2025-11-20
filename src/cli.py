import sys
import os
import getpass
import tkinter as tk
from tkinter import filedialog
from vault import VaultManager
from gui import select_files, select_folder, select_save_location
from file_ops import FileOperations

def get_password(prompt="Enter Vault Password: "):
    return getpass.getpass(prompt)

def handle_command(args):
    vault = VaultManager()
    file_ops = FileOperations(vault)

    # Check if vault exists
    # Allowed commands when vault doesn't exist: help, setup, imp (to restore), format (to verify clean)
    if not vault.is_exists() and args.command not in ['help', 'setup', 'imp', 'format']:
        print("Vault not found. Please run 'abc setup' first.")
        return

    # Session Management
    if args.command == 'setup':
        # Handled below
        pass
    elif args.command == 'lock':
        vault.lock()
        return
    elif args.command == 'unlock':
        pass
    elif args.command == 'imp':
        pass
    elif args.command == 'exp':
        pass
    elif args.command == 'help':
        pass
    else:
        # For other commands, check if unlocked (session key exists)
        if not vault.is_unlocked():
            print("Vault is locked. Please run 'abc unlock' first.")
            return
        else:
            # Vault is unlocked, load session key
            key_path = os.path.join(vault.vault_dir, '.session_key')
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    key = f.read()
                from crypto import CryptoManager
                file_ops.crypto = CryptoManager(key=key)
            else:
                print("Session error. Please lock and unlock again.")
                return

    # Now execute command
    if args.command == 'setup':
        try:
            if vault.is_exists():
                print("Vault already exists. Run 'abc unlock' to access it.")
            else:
                print("Starting Vault Setup...")
                pwd = get_password("Set New Vault Password: ")
                confirm = get_password("Confirm Password: ")
                if pwd != confirm:
                    print("Passwords do not match.")
                    input("Press Enter to exit...")
                    return
                vault.create_vault(pwd)
                # Init crypto to create session key immediately? 
                # No, user should unlock or we can auto-unlock.
                # Let's auto-unlock.
                file_ops.init_crypto(pwd)
                key_path = os.path.join(vault.vault_dir, '.session_key')
                with open(key_path, 'wb') as f:
                    f.write(file_ops.crypto.key)
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(key_path, 0x02)
                
                print("Vault setup complete.")
        except Exception as e:
            print(f"Setup failed: {e}")
        
        input("Press Enter to exit...")

    elif args.command == 'unlock':
        if vault.is_unlocked():
            print("Vault is already unlocked.")
        else:
            pwd = get_password()
            if vault.unlock(pwd):
                file_ops.init_crypto(pwd)
                # Save session key
                key_path = os.path.join(vault.vault_dir, '.session_key')
                with open(key_path, 'wb') as f:
                    f.write(file_ops.crypto.key)
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(key_path, 0x02)
                print("Vault unlocked.")
        
    elif args.command == 'store':
        # Ask user if file or folder
        print("Select file or folder to store:")
        print("1. File")
        print("2. Folder")
        choice = input("Choice (1/2): ")
        if choice == '1':
            path = select_files()
        elif choice == '2':
            path = select_folder()
        else:
            print("Invalid choice.")
            return
            
        if path:
            file_ops.store(path)
            
    elif args.command == 'move':
        print("Select file/folder from Vault to move...")
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        print("1. Move File")
        print("2. Move Folder")
        choice = input("Choice (1/2): ")
        
        vault_root = vault.get_vault_root()
        path = None
        if choice == '1':
            path = filedialog.askopenfilename(initialdir=vault_root, title="Select File in Vault")
        elif choice == '2':
            path = filedialog.askdirectory(initialdir=vault_root, title="Select Folder in Vault")
            
        if path:
            # Check if path is actually inside vault
            if not os.path.abspath(path).startswith(os.path.abspath(vault_root)):
                print("Error: Selected file is not inside the vault.")
                return
                
            # Get relative name
            name = os.path.relpath(path, vault_root)
            
            # Select destination
            print("Select destination folder...")
            dest = select_save_location()
            if dest:
                file_ops.move(name, dest)

    elif args.command == 'del':
        name = input("Enter file/folder name to delete (relative to vault root): ")
        file_ops.delete(name)

    elif args.command == 'format':
        if not vault.is_exists():
            print("Vault does not exist (already clean).")
        else:
            file_ops.format_vault()

    elif args.command == 'destroy':
        if not vault.is_exists():
            print("Vault does not exist.")
        else:
            file_ops.destroy_vault()

    elif args.command == 'backups':
        while True:
            print("\n--- Backup Management ---")
            backups = file_ops.get_backups()
            if not backups:
                print("No backups found.")
                break
                
            for i, item in enumerate(backups, 1):
                print(f" [{i}] {item}")
            
            print("\nOptions:")
            print(" [ID] Enter number to delete specific backup")
            print(" [A]  Delete ALL backups")
            print(" [Q]  Quit/Back")
            
            choice = input("Choice: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'a':
                confirm = input("Are you sure you want to delete ALL backups? (y/n): ")
                if confirm.lower() == 'y':
                    file_ops.delete_all_backups()
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(backups):
                    file_ops.delete_backup(backups[idx])
                else:
                    print("Invalid ID.")
            else:
                print("Invalid choice.")

    elif args.command == 'list':
        file_ops.list_files()
        
    elif args.command == 'imp':
        print("Select vault export file (.zip)...")
        path = select_files()
        if path:
            if vault.is_exists():
                print("Vault already exists.")
                print("1. Overwrite (Deletes current vault and replaces it)")
                print("2. Merge (Adds files - ONLY works if passwords match)")
                choice = input("Choice (1/2): ")
                if choice == '2':
                    file_ops.import_vault(path, merge=True)
                elif choice == '1':
                    file_ops.import_vault(path, merge=False)
                else:
                    print("Cancelled.")
            else:
                file_ops.import_vault(path, merge=False)
        
    elif args.command == 'exp':
        print("Select destination folder for export...")
        dest = select_save_location()
        if dest:
            print("Export Options:")
            print("1. Export and keep original data")
            print("2. Export and DELETE all original data")
            choice = input("Choice (1/2): ")
            
            delete_after = (choice == '2')
            file_ops.export_vault(dest, delete_after)

    elif args.command == 'help':
        print("Help:")
        print(" abc store   - Store file/folder")
        print(" abc move    - Move file/folder out")
        print(" abc del     - Delete file/folder")
        print(" abc lock    - Lock vault")
        print(" abc unlock  - Unlock vault")
        print(" abc format  - Empty vault (keeps structure)")
        print(" abc destroy - Destroy vault completely")
        print(" abc imp/exp - Import/Export vault")
