import ctypes
import os
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ensure_hidden_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        # Set hidden attribute
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)
