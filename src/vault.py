import os
import sys
import hashlib
import secrets
from utils import ensure_hidden_dir

class VaultManager:
    def __init__(self):
        # Hidden vault location - disguised as Windows service folder
        # Located in: C:\Users\<username>\AppData\Roaming\Microsoft\Windows\.winsvc
        appdata = os.environ['APPDATA']
        self.vault_dir = os.path.join(appdata, 'Microsoft', 'Windows', '.winsvc')
        self.config_path = os.path.join(self.vault_dir, 'config.dat')
        
    def is_exists(self):
        return os.path.exists(self.config_path)

    def is_unlocked(self):
        # Check if the session key exists
        session_key_path = os.path.join(self.vault_dir, '.session_key')
        return os.path.exists(session_key_path)

    def create_vault(self, password):
        ensure_hidden_dir(self.vault_dir)
        
        if self.is_exists():
            print("Vault already exists.")
            return

        print("Creating new vault...")
        
        # 1. Generate Salt
        salt = secrets.token_bytes(16)
        
        # 2. Hash Password with Salt using PBKDF2-HMAC-SHA256
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        
        # 3. Save Salt and Hash
        with open(self.config_path, 'wb') as f:
            f.write(salt)  # 16 bytes
            f.write(dk)    # 32 bytes
            
        # Hide config
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(self.config_path, 0x02)
        
        print(f"Vault created at {self.vault_dir}")

    def verify_password(self, password):
        if not self.is_exists():
            return False
            
        with open(self.config_path, 'rb') as f:
            salt = f.read(16)
            stored_hash = f.read(32)
            
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return secrets.compare_digest(dk, stored_hash)

    def get_salt(self):
        if not self.is_exists():
            return None
        with open(self.config_path, 'rb') as f:
            salt = f.read(16)
        return salt

    def unlock(self, password):
        if self.verify_password(password):
            print("Password verified.")
            return True
        else:
            print("Incorrect password.")
            return False

    def lock(self):
        print("Locking vault...")
        session_key_path = os.path.join(self.vault_dir, '.session_key')
        if os.path.exists(session_key_path):
            os.remove(session_key_path)
        print("Vault locked.")

    def get_vault_root(self):
        return self.vault_dir
