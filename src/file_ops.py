import os
import shutil
import datetime
import json
from crypto import CryptoManager
from vault import VaultManager

class FileOperations:
    def __init__(self, vault_manager: VaultManager):
        self.vault = vault_manager
        self.crypto = None
        # Initialize filename map path here (so it's available even when loading from session)
        self.filename_map_path = os.path.join(self.vault.vault_dir, '.filename_map.json')

    def init_crypto(self, password):
        """Initialize crypto with password and load filename mappings."""
        try:
            # Get salt from vault config
            salt = self.vault.get_salt()
            if not salt:
                raise Exception("Vault corrupted or missing salt.")
            
            self.crypto = CryptoManager()
            # Generate key using the same password and salt
            key, _ = self.crypto.generate_key(password, salt)
            self.crypto.key = key
            self.crypto.chacha = __import__('cryptography.hazmat.primitives.ciphers.aead', fromlist=['ChaCha20Poly1305']).ChaCha20Poly1305(key)
        except Exception as e:
            raise Exception(f"Crypto initialization failed: {e}")

    def _load_filename_map(self):
        """Load filename mapping from vault."""
        try:
            if not os.path.exists(self.filename_map_path):
                return {}
            
            with open(self.filename_map_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load filename map: {e}")
            return {}

    def _save_filename_map(self, mapping):
        """Save filename mapping to vault."""
        try:
            import ctypes
            
            # Unhide file if it exists (to allow writing)
            if os.path.exists(self.filename_map_path):
                ctypes.windll.kernel32.SetFileAttributesW(self.filename_map_path, 0x80)  # Normal
            
            # Write mapping
            with open(self.filename_map_path, 'w') as f:
                json.dump(mapping, f, indent=2)
            
            # Hide the mapping file again
            ctypes.windll.kernel32.SetFileAttributesW(self.filename_map_path, 0x02)  # Hidden
        except Exception as e:
            raise Exception(f"Failed to save filename map: {e}")

    def _add_filename_mapping(self, encrypted_name, original_name):
        """Add a mapping from encrypted filename to original filename."""
        try:
            mapping = self._load_filename_map()
            mapping[encrypted_name] = original_name  # encrypted -> original
            self._save_filename_map(mapping)
        except Exception as e:
            print(f"Warning: Could not save filename mapping: {e}")

    def _get_original_filename(self, encrypted_name):
        """Get original filename from encrypted name."""
        try:
            mapping = self._load_filename_map()
            return mapping.get(encrypted_name, encrypted_name)  # Fallback to encrypted name
        except Exception as e:
            return encrypted_name  # Fallback on error

    def store(self, path):
        if not self.vault.is_unlocked():
            raise Exception("Vault is locked.")
        
        if not self.crypto:
            raise Exception("Crypto not initialized. Please unlock first.")

        if os.path.isfile(path):
            self._store_file(path)
        elif os.path.isdir(path):
            self._store_folder(path)
        else:
            print(f"Invalid path: {path}")

    def _store_file(self, path):
        """Store file with encrypted filename (Layer 1) and encrypted content (Layers 2+3)."""
        try:
            filename = os.path.basename(path)
            
            # Layer 1: Encrypt filename
            encrypted_filename = self.crypto.encrypt_filename(filename)
            dest_path = os.path.join(self.vault.get_vault_root(), encrypted_filename)
            
            print(f"Encrypting and storing {filename}...")
            
            # Layers 2+3: Encrypt file content (AES + ChaCha20)
            self.crypto.encrypt_file(path, dest_path)
            
            # Save filename mapping (encrypted -> original)
            self._add_filename_mapping(encrypted_filename, filename)
            
            # Verify success then delete original
            if os.path.exists(dest_path):
                os.remove(path)
                print(f"Stored {filename} securely (3-layer encryption).")
            else:
                print(f"Failed to store {filename}.")
        except Exception as e:
            print(f"Error storing {filename}: {e}")

    def _store_folder(self, path):
        dirname = os.path.basename(path)
        dest_dir = os.path.join(self.vault.get_vault_root(), dirname)
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        for root, dirs, files in os.walk(path):
            # Create corresponding structure in vault
            rel_path = os.path.relpath(root, path)
            current_dest_dir = os.path.join(dest_dir, rel_path)
            
            if not os.path.exists(current_dest_dir):
                os.makedirs(current_dest_dir)
                
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(current_dest_dir, file)
                print(f"Encrypting {file}...")
                self.crypto.encrypt_file(src_file, dest_file)
        
        # Remove original folder
        shutil.rmtree(path)
        print(f"Stored folder {dirname}.")

    def move(self, name, dest):
        """Move (decrypt and extract) file or folder from vault to destination."""
        try:
            # Get the encrypted path from vault
            vault_root = self.vault.get_vault_root()
            source_path = os.path.join(vault_root, name)
            
            if not os.path.exists(source_path):
                print(f"'{name}' not found in vault.")
                return
            
            if os.path.isfile(source_path):
                # Handle file
                original_filename = self._get_original_filename(name)
                
                # Create temporary decrypted file
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, original_filename)
                
                print(f"Decrypting and moving {original_filename}...")
                
                # Decrypt the file (3-layer decryption: ChaCha20 -> AES -> plaintext)
                self.crypto.decrypt_file(source_path, temp_path)
                
                # Move decrypted file to destination
                final_dest = os.path.join(dest, original_filename)
                shutil.move(temp_path, final_dest)
                
                # Remove encrypted file from vault
                os.remove(source_path)
                
                # Remove from filename mapping
                mapping = self._load_filename_map()
                if name in mapping:
                    del mapping[name]
                    self._save_filename_map(mapping)
                
                print(f"Moved {original_filename} to {dest}.")
                
            elif os.path.isdir(source_path):
                # Handle folder
                print(f"Decrypting and moving folder {name}...")
                
                # Create destination folder
                dest_folder = os.path.join(dest, name)
                if not os.path.exists(dest_folder):
                    os.makedirs(dest_folder)
                
                # Decrypt all files in the folder recursively
                for root, dirs, files in os.walk(source_path):
                    rel_path = os.path.relpath(root, source_path)
                    current_dest_dir = os.path.join(dest_folder, rel_path) if rel_path != '.' else dest_folder
                    
                    if not os.path.exists(current_dest_dir):
                        os.makedirs(current_dest_dir)
                    
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(current_dest_dir, file)
                        print(f"Decrypting {file}...")
                        self.crypto.decrypt_file(src_file, dest_file)
                
                # Remove encrypted folder from vault
                shutil.rmtree(source_path)
                print(f"Moved folder {name} to {dest}.")
                
        except Exception as e:
            print(f"Error moving file: {e}")

    def delete(self, name):
        
        source_path = os.path.join(self.vault.get_vault_root(), name)
        if not os.path.exists(source_path):
            print(f"Not found: {name}")
            return
            
        backup_dir = os.path.join(self.vault.get_vault_root(), ".backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            # Hide it
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(backup_dir, 0x02)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}"
        dest_path = os.path.join(backup_dir, backup_name)
        
        shutil.move(source_path, dest_path)
        print(f"Deleted {name} (Moved to backups).")

    def delete_all(self):
        root = self.vault.get_vault_root()
        for item in os.listdir(root):
            if item in ['.salt', '.backups', 'System Volume Information', '$RECYCLE.BIN', 'config.dat', '.session_key']:
                continue
            path = os.path.join(root, item)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                print(f"Failed to delete {path}. Reason: {e}")
        print("All files deleted from vault.")
    def get_backups(self):
        backup_dir = os.path.join(self.vault.vault_dir, '.backups')
        if not os.path.exists(backup_dir):
            return []
        return os.listdir(backup_dir)

    def list_backups(self):
        backups = self.get_backups()
        if not backups:
            print("No backups found.")
            return

        print("Backups:")
        for i, item in enumerate(backups, 1):
            print(f" [{i}] {item}")

    def format_vault(self):
        # "abc format -> with '5 sec cooldown time' it will format full vault."
        print("WARNING: This will erase ALL data in the vault.")
        print("Press Ctrl+C to cancel. Starting in...")
        import time
        try:
            for i in range(5, 0, -1):
                print(f"{i}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nFormat cancelled.")
            return
            
        self.delete_all()
        # Also delete backups
        backup_dir = os.path.join(self.vault.get_vault_root(), ".backups")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        print("Vault formatted (all data deleted).")

    def destroy_vault(self):
        print("WARNING: This will COMPLETELY DESTROY the vault.")
        print("You will need to run 'abc setup' again to create a new vault.")
        print("Press Ctrl+C to cancel. Starting in...")
        import time
        try:
            for i in range(5, 0, -1):
                print(f"{i}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDestroy cancelled.")
            return
            
        vault_dir = self.vault.vault_dir
        if os.path.exists(vault_dir):
            shutil.rmtree(vault_dir)
            print("Vault destroyed. Run 'abc setup' to create a new vault.")
        else:
            print("Vault does not exist.")

    def delete_backup(self, filename):
        backup_path = os.path.join(self.vault.vault_dir, '.backups', filename)
        try:
            if os.path.isdir(backup_path):
                shutil.rmtree(backup_path)
            else:
                os.remove(backup_path)
            print(f"Deleted backup: {filename}")
        except Exception as e:
            print(f"Error deleting backup: {e}")

    def delete_all_backups(self):
        backup_dir = os.path.join(self.vault.vault_dir, '.backups')
        if not os.path.exists(backup_dir):
            print("No backups to delete.")
            return
            
        try:
            shutil.rmtree(backup_dir)
            os.makedirs(backup_dir)
            # Hide it again
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(backup_dir, 0x02)
            print("All backups deleted.")
        except Exception as e:
            print(f"Error deleting backups: {e}")

    def list_files(self):
        """List files in vault with decrypted original filenames."""
        if not self.vault.is_unlocked():
            print("Vault is locked. Please unlock first.")
            return

        root = self.vault.get_vault_root()
        print(f"Listing files in Vault ({root}):")
        print("-" * 30)
        
        count = 0
        for item in os.listdir(root):
            # Skip internal files
            if item in ['.salt', '.session_key', '.backups', 'config.dat', '.filename_map.json', 'System Volume Information', '$RECYCLE.BIN']:
                continue
            
            path = os.path.join(root, item)
            
            # Get original filename from mapping
            original_name = self._get_original_filename(item)
            
            if os.path.isdir(path):
                print(f"[DIR]  {original_name}")
            else:
                size = os.path.getsize(path)
                print(f"[FILE] {original_name} ({size} bytes)")
            count += 1
            
        if count == 0:
            print("(Vault is empty)")
        print("-" * 30)

    def export_vault(self, dest_folder, delete_after=False):
        if self.vault.is_unlocked():
            print("Please lock the vault before exporting.")
            return

        vault_dir = self.vault.vault_dir
        if not os.path.exists(vault_dir):
            print("No vault found to export.")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # We want the zip file to be named abc_vault_export_TIMESTAMP.zip
        base_name = os.path.join(dest_folder, f"abc_vault_export_{timestamp}")

        try:
            # Create zip archive
            # root_dir is the parent of vault_dir, base_dir is the vault_dir name
            # This ensures the zip contains the folder 'abc_vault' (or whatever) inside it?
            # Actually, let's just zip the contents of vault_dir.
            # shutil.make_archive(base_name, 'zip', vault_dir)
            # But we want to exclude .session_key if possible. make_archive doesn't support ignore.
            # So we can copy to temp, remove key, zip, remove temp.
            # Or just zip everything. .session_key is harmless if locked (it's deleted on lock).
            
            shutil.make_archive(base_name, 'zip', vault_dir)
            print(f"Vault exported to {base_name}.zip")
            
            if delete_after:
                print("Deleting original vault data...")
                # We delete the vault directory entirely? Or just contents?
                # "exp and dele all data" implies clearing the vault.
                # Let's remove the vault directory.
                shutil.rmtree(vault_dir)
                print("Original vault deleted.")
                
        except Exception as e:
            print(f"Export failed: {e}")

    def import_vault(self, source_path, merge=False):
        if self.vault.is_unlocked():
            print("Please lock the current vault before importing.")
            return
            
        # source_path should be the zip file
        if not source_path.lower().endswith('.zip'):
            print("Invalid source. Please select the exported .zip file.")
            return
        
        if not os.path.exists(source_path):
            print("Source file not found.")
            return
        
        try:
            if merge:
                # Merge mode - only works with same password
                print("Merging vault...")
                import tempfile
                temp_extract = tempfile.mkdtemp()
                
                try:
                    shutil.unpack_archive(source_path, temp_extract, 'zip')
                    
                    # Check password compatibility
                    imported_config = os.path.join(temp_extract, 'config.dat')
                    if not os.path.exists(imported_config):
                        print("Invalid vault export.")
                        return
                    
                    with open(imported_config, 'rb') as f:
                        imported_salt = f.read(16)
                    
                    current_salt = self.vault.get_salt()
                    
                    if imported_salt != current_salt:
                        # Different passwords - ask for imported vault password
                        print("\n⚠ IMPORTED VAULT HAS A DIFFERENT PASSWORD")
                        print("To merge, you need to provide BOTH passwords:")
                        print("  1. The password of the IMPORTED vault (to decrypt)")
                        print("  2. Your CURRENT vault password (to re-encrypt)")
                        
                        import getpass
                        
                        # Get imported vault password
                        imported_password = getpass.getpass("\nEnter IMPORTED vault password: ")
                        
                        # Verify imported password
                        with open(imported_config, 'rb') as f:
                            imported_salt = f.read(16)
                            imported_hash = f.read(32)
                        
                        import hashlib
                        dk = hashlib.pbkdf2_hmac('sha256', imported_password.encode(), imported_salt, 100000)
                        if dk != imported_hash:
                            print("✗ ERROR: Incorrect password for imported vault.")
                            return
                        
                        # Get current vault password
                        current_password = getpass.getpass("Enter CURRENT vault password: ")
                        
                        if not self.vault.verify_password(current_password):
                            print("✗ ERROR: Incorrect current vault password.")
                            return
                        
                        print("\n🔄 Re-encrypting files with your current password...")
                        
                        # Initialize crypto for both keys
                        from crypto import CryptoManager
                        
                        # Old crypto (imported vault)
                        old_crypto = CryptoManager()
                        old_key, _ = old_crypto.generate_key(imported_password, imported_salt)
                        old_crypto.key = old_key
                        old_crypto.chacha = __import__('cryptography.hazmat.primitives.ciphers.aead', fromlist=['ChaCha20Poly1305']).ChaCha20Poly1305(old_key)
                        
                        # New crypto (current vault)
                        new_crypto = CryptoManager()
                        new_key, _ = new_crypto.generate_key(current_password, current_salt)
                        new_crypto.key = new_key
                        new_crypto.chacha = __import__('cryptography.hazmat.primitives.ciphers.aead', fromlist=['ChaCha20Poly1305']).ChaCha20Poly1305(new_key)
                        
                        # Re-encrypt files
                        vault_root = self.vault.vault_dir
                        file_count = 0
                        
                        import tempfile as tmp
                        temp_decrypt_dir = tmp.mkdtemp()
                        
                        try:
                            for item in os.listdir(temp_extract):
                                if item in ['config.dat', '.session_key', '.backups', 'System Volume Information', '$RECYCLE.BIN']:
                                    continue
                                
                                source_file = os.path.join(temp_extract, item)
                                if os.path.isfile(source_file):
                                    # Decrypt with old password
                                    temp_decrypt = os.path.join(temp_decrypt_dir, f"temp_{item}")
                                    try:
                                        old_crypto.decrypt_file(source_file, temp_decrypt)
                                        
                                        # Re-encrypt with new password
                                        dest_file = os.path.join(vault_root, item)
                                        new_crypto.encrypt_file(temp_decrypt, dest_file)
                                        
                                        file_count += 1
                                        print(f"  ✓ Re-encrypted: {item}")
                                    except Exception as e:
                                        print(f"  ✗ Failed to process {item}: {e}")
                            
                            # Merge filename mappings
                            imported_mapping_file = os.path.join(temp_extract, '.filename_map.json')
                            if os.path.exists(imported_mapping_file):
                                current_mapping_file = os.path.join(vault_root, '.filename_map.json')
                                
                                import json
                                with open(imported_mapping_file, 'r') as f:
                                    imported_mapping = json.load(f)
                                
                                if os.path.exists(current_mapping_file):
                                    # Unhide to read
                                    import ctypes
                                    ctypes.windll.kernel32.SetFileAttributesW(current_mapping_file, 0x80)
                                    
                                    with open(current_mapping_file, 'r') as f:
                                        current_mapping = json.load(f)
                                    current_mapping.update(imported_mapping)
                                else:
                                    current_mapping = imported_mapping
                                
                                # Save merged mapping
                                with open(current_mapping_file, 'w') as f:
                                    json.dump(current_mapping, f, indent=2)
                                
                                # Hide again
                                import ctypes
                                ctypes.windll.kernel32.SetFileAttributesW(current_mapping_file, 0x02)
                            
                            print(f"\n✓ Successfully merged {file_count} files!")
                            print("  All files have been re-encrypted with your current password.")
                            
                        finally:
                            shutil.rmtree(temp_decrypt_dir)
                        
                        return
                    
                    # Same password - safe to merge
                    vault_root = self.vault.vault_dir
                    file_count = 0
                    
                    for item in os.listdir(temp_extract):
                        if item in ['config.dat', '.session_key']:
                            continue
                        
                        source = os.path.join(temp_extract, item)
                        dest = os.path.join(vault_root, item)
                        
                        if os.path.isfile(source):
                            shutil.copy2(source, dest)
                            file_count += 1
                        elif os.path.isdir(source):
                            if os.path.exists(dest):
                                shutil.rmtree(dest)
                            shutil.copytree(source, dest)
                    
                    print(f"✓ Merged {file_count} items into vault.")
                    
                finally:
                    shutil.rmtree(temp_extract)
            else:
                # Overwrite mode
                vault_dir = self.vault.vault_dir
                if os.path.exists(vault_dir):
                    shutil.rmtree(vault_dir)
                
                os.makedirs(vault_dir)
                shutil.unpack_archive(source_path, vault_dir, 'zip')
                
                # Hide vault
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(vault_dir, 0x02)
                print("✓ Vault imported (overwrite).")
                
        except Exception as e:
            print(f"Import failed: {e}")
