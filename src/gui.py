import tkinter as tk
from tkinter import filedialog
import os

def select_files():
    root = tk.Tk()
    root.withdraw() # Hide main window
    root.attributes('-topmost', True) # Bring to front
    file_path = filedialog.askopenfilename(title="Select File to Store")
    return file_path

def select_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(title="Select Folder to Store")
    return folder_path

def select_save_location():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(title="Select Destination Folder")
    return folder_path
