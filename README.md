# SHADO - Triple-Layer Stealth Vault

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Description / Overview

**SHADO** (*Shadow*) is a secure, hidden encryption vault designed exclusively for Windows. It employs a robust **3-layer encryption system** to ensure your data remains private and secure.

> **Note**: This project was developed with the assistance of AI. While core logic and architecture were designed collaboratively, code has been reviewed, modified, and adapted to meet specific security and functionality requirements.

---

**Security Architecture:**
1. **Layer 1**: Filename Encryption (SHA-256 hashing - hides file metadata)
2. **Layer 2**: AES-256-GCM (industry-standard content encryption)
3. **Layer 3**: ChaCha20-Poly1305 (second-pass content encryption)

**Stealth Features:**
- **Hidden Location**: `%APPDATA%\Microsoft\Windows\.winsvc` (disguised as Windows service)
- **Filename Obfuscation**: Files appear as `a7f3e9c2d1b8.enc` instead of `passwords.txt`
- **Anti-Detection**: Blends in with legitimate Windows system files

**Authentication**: PBKDF2-HMAC-SHA256 password verification (100,000 iterations)

**WINDOWS ONLY**: SHADO is exclusively designed for Windows and uses Windows-specific features like `SetFileAttributesW` and the AppData folder structure.

---

## Installation

### Prerequisites
- **Windows 10/11** (required)
- **Python 3.8+**

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/SHADO.git
   cd SHADO
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add to PATH (optional):**
   - Add the project directory to your system PATH, or
   - Use the provided `abc.bat` wrapper

**Vault Location:** `C:\Users\<YourUsername>\AppData\Roaming\Microsoft\Windows\.winsvc`

---

## Usage

### 1. Setup (First Run)
Initialize the vault and set your password:
```bash
abc setup
```

### 2. Unlock
Unlock the vault before operations:
```bash
abc unlock
```

### 3. Store Files
Encrypt and store files (3-layer encryption). A file picker dialog will appear.
```bash
abc store
```

### 4. List Files
View vault contents with **original filenames** (decrypted for display):
```bash
abc list
```

### 5. Move (Retrieve)
Decrypt and extract files from vault (supports both files and folders):
```bash
abc move
```

### 6. Lock
Lock the vault to prevent access:
```bash
abc lock
```

### 7. Export Vault
Backup entire vault to ZIP:
```bash
abc exp
```
**Options:**
- Export only
- Export and delete original data

### 8. Import Vault
Restore from ZIP backup:
```bash
abc imp
```
**Import Modes:**
- **Overwrite**: Replace current vault
- **Merge (Same Password)**: Direct merge
- **Merge (Different Password)**: Smart re-encryption (Asks for both passwords and automatically re-encrypts files)

### 9. Manage Backups
Interactive backup management:
```bash
abc backups
```

### 10. Delete Files
Delete with backup (moved to `.backups` folder):
```bash
abc del
```

### 11. Format Vault
Erase all data (5-second safety delay):
```bash
abc format
```

### 12. Destroy Vault
Completely remove vault (requires `abc setup` to recreate):
```bash
abc destroy
```

---

## Features

- **Triple-Layer Encryption** - Filename + AES-256 + ChaCha20
- **Stealth Location** - Hidden in Windows system folders
- **Cross-Vault Merging** - Merge vaults with different passwords (auto re-encryption)
- **Smart Backups** - Backup-on-delete with interactive management
- **Import/Export** - Full vault backup to ZIP
- **CLI + GUI** - Fast command-line with file picker dialogs
- **No Admin Rights** - Runs without Administrator privileges

---

## Tech Stack / Built With

- **Language**: Python 3.8+
- **Platform**: Windows
- **Cryptography**: `cryptography` library (AES-GCM, ChaCha20-Poly1305, PBKDF2)
- **GUI**: Tkinter (for file dialogs)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

**Guidelines:**
1. Open an issue to discuss major changes
2. Follow existing code style
3. Add error handling for new features
4. Test thoroughly before submitting
5. Update documentation as needed

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Credits / Acknowledgments

- **Development**: Created with AI assistance
- **Cryptography**: Built on the excellent [cryptography](https://cryptography.io/) library
- **Inspiration**: Designed for users who need simple, secure file encryption without BitLocker complexity

---

## Disclaimer

This software is provided **"as is"** without warranty. While it uses industry-standard encryption algorithms, the authors are not responsible for any data loss. **Always keep backups of important data.**

**Remember**: If you lose your password, your data is **unrecoverable**. There is no backdoor or password recovery mechanism.
