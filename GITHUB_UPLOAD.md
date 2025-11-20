# GitHub Upload Guide

## Method 1: Using Git Commands (Recommended)

### First Time Setup:
1. **Initialize Git repository:**
   ```bash
   cd S:\cmd-encfol
   git init
   ```

2. **Add all files:**
   ```bash
   git add .
   ```

3. **Create initial commit:**
   ```bash
   git commit -m "Initial commit: 3-layer encrypted vault with stealth location"
   ```

4. **Create repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `windows-encryption-vault` (or your choice)
   - Description: `A secure 3-layer encryption vault for Windows with stealth location`
   - Keep it **Public** or **Private** (your choice)
   - **DO NOT** initialize with README, .gitignore, or license (you already have these)
   - Click "Create repository"

5. **Link to GitHub and push:**
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/REPO-NAME.git
   git branch -M main
   git push -u origin main
   ```

### Future Updates:
```bash
git add .
git commit -m "Your commit message"
git push
```

---

## Method 2: Using GitHub Website (Manual Upload)

1. **Go to GitHub:**
   - Navigate to https://github.com/new
   - Create new repository with same settings as above

2. **Upload files:**
   - Click "uploading an existing file"
   - Drag and drop ALL files/folders from `S:\cmd-encfol`
   - **IMPORTANT**: Make sure to upload:
     - ✅ `src/` folder (all Python files)
     - ✅ `abc.bat`
     - ✅ `requirements.txt`
     - ✅ `README.md`
     - ✅ `LICENSE`
     - ✅ `.gitignore`
   - Add commit message: "Initial commit: 3-layer vault"
   - Click "Commit changes"

---

## ⚠️ Important Notes

- **Never commit** your actual vault (`.abc_vault` folder) - it's already in `.gitignore`
- **Never commit** `__pycache__` or `.venv` - also in `.gitignore`
- Your vault data stays **local and encrypted** on your PC
- Only the **source code** goes to GitHub

---

## Recommended Repository Settings

After uploading, add these to your GitHub repo:

### Topics (for discoverability):
- `python`
- `encryption`
- `security`
- `windows`
- `vault`
- `aes-encryption`
- `chacha20`

### Description:
```
A secure 3-layer encryption vault for Windows with filename obfuscation, 
stealth location, and cross-vault merging. Security rating: 9.5/10
```

---

## Quick Reference

**Your Repository URL will be:**
```
https://github.com/YOUR-USERNAME/REPO-NAME
```

**Clone command for others:**
```bash
git clone https://github.com/YOUR-USERNAME/REPO-NAME.git
```
