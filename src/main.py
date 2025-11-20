import sys
import argparse
from vault import VaultManager
from cli import handle_command

def main():
    parser = argparse.ArgumentParser(description="Windows Encryption Vault (abc)")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Define commands
    subparsers.add_parser('store', help='Store a file or folder in the vault')
    subparsers.add_parser('move', help='Move a file or folder from the vault')
    subparsers.add_parser('del', help='Delete a file or folder from the vault')
    subparsers.add_parser('lock', help='Lock the vault')
    subparsers.add_parser('unlock', help='Unlock the vault')
    subparsers.add_parser('list', help='List files in the vault')
    subparsers.add_parser('setup', help='Create a new vault')
    subparsers.add_parser('format', help='Empty the vault (delete all files and backups)')
    subparsers.add_parser('destroy', help='Completely destroy the vault (requires setup again)')
    subparsers.add_parser('imp', help='Import vault from backup')
    subparsers.add_parser('exp', help='Export vault to backup')
    subparsers.add_parser('backups', help='Manage backups')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    handle_command(args)

if __name__ == "__main__":
    main()
