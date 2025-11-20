import os
import sys

def check_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'rb') as f:
        header = f.read(12) # Nonce
        tag = f.read(16)    # Tag
        content = f.read(32) # First 32 bytes of content
    
    print(f"File: {path}")
    print(f"Nonce: {header.hex()}")
    print(f"Tag: {tag.hex()}")
    print(f"Content Start: {content.hex()}")
    
    # Heuristic: If it's a JPG, it should start with FF D8 FF
    if content.hex().upper().startswith("FFD8FF"):
        print("WARNING: Looks like a valid JPG header! File might NOT be encrypted.")
    else:
        print("File does not look like a standard image format (Good).")

if __name__ == "__main__":
    # Check the file in the vault
    vault_dir = os.path.join(os.environ['USERPROFILE'], '.abc_vault')
    # Find a file
    for f in os.listdir(vault_dir):
        if f.endswith('.jpg'):
            check_file(os.path.join(vault_dir, f))
