import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import hashlib

class CryptoManager:
    def __init__(self, key=None):
        self.key = key  # 32-byte key for AES-256
        self.chacha = None
        if key:
            self.chacha = ChaCha20Poly1305(key)

    def generate_key(self, password, salt=None):
        """Generate AES key from password using PBKDF2."""
        try:
            if salt is None:
                salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(password.encode())
            return key, salt
        except Exception as e:
            raise Exception(f"Key generation failed: {e}")

    def encrypt_filename(self, filename):
        """Encrypt filename to hide metadata (Layer 1)."""
        try:
            if not self.key:
                raise Exception("Encryption key not set")
            
            # Use hash-based deterministic encryption for filenames
            # This ensures same filename always maps to same encrypted name
            hash_obj = hashlib.sha256(self.key + filename.encode())
            encrypted_name = hash_obj.hexdigest()[:32]  # 32 chars for filename
            return encrypted_name + ".enc"
        except Exception as e:
            raise Exception(f"Filename encryption failed: {e}")

    def encrypt_file(self, input_path, output_path):
        """
        3-Layer Encryption:
        1. Read plaintext file
        2. Layer 2: Encrypt with AES-256-GCM
        3. Layer 3: Encrypt with ChaCha20-Poly1305
        """
        try:
            if not self.key:
                raise Exception("Encryption key not set")
            
            # Read original file
            with open(input_path, 'rb') as f:
                plaintext = f.read()
            
            # Layer 2: AES-256-GCM
            aesgcm = AESGCM(self.key)
            nonce_aes = os.urandom(12)
            ciphertext_aes = aesgcm.encrypt(nonce_aes, plaintext, None)
            
            # Layer 3: ChaCha20-Poly1305
            if not self.chacha:
                self.chacha = ChaCha20Poly1305(self.key)
            nonce_chacha = os.urandom(12)
            ciphertext_final = self.chacha.encrypt(nonce_chacha, ciphertext_aes, None)
            
            # Write: [nonce_aes(12)][nonce_chacha(12)][ciphertext_final]
            with open(output_path, 'wb') as f:
                f.write(nonce_aes)
                f.write(nonce_chacha)
                f.write(ciphertext_final)
                
        except FileNotFoundError:
            raise Exception(f"Input file not found: {input_path}")
        except PermissionError:
            raise Exception(f"Permission denied: {output_path}")
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")

    def decrypt_file(self, input_path, output_path):
        """
        3-Layer Decryption (reverse order):
        1. Read encrypted file
        2. Layer 3: Decrypt ChaCha20-Poly1305
        3. Layer 2: Decrypt AES-256-GCM
        """
        try:
            if not self.key:
                raise Exception("Decryption key not set")
            
            # Read encrypted file
            with open(input_path, 'rb') as f:
                nonce_aes = f.read(12)
                nonce_chacha = f.read(12)
                ciphertext_final = f.read()
            
            if len(nonce_aes) != 12 or len(nonce_chacha) != 12:
                raise Exception("Corrupted file: Invalid nonce size")
            
            # Layer 3: Decrypt ChaCha20-Poly1305
            if not self.chacha:
                self.chacha = ChaCha20Poly1305(self.key)
            ciphertext_aes = self.chacha.decrypt(nonce_chacha, ciphertext_final, None)
            
            # Layer 2: Decrypt AES-256-GCM
            aesgcm = AESGCM(self.key)
            plaintext = aesgcm.decrypt(nonce_aes, ciphertext_aes, None)
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(plaintext)
                
        except FileNotFoundError:
            raise Exception(f"Encrypted file not found: {input_path}")
        except PermissionError:
            raise Exception(f"Permission denied: {output_path}")
        except Exception as e:
            # Check if it's a decryption failure (wrong password)
            if "AEAD" in str(e) or "MAC" in str(e):
                raise Exception("Decryption failed: Wrong password or corrupted file")
            raise Exception(f"Decryption failed: {e}")
