import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
from datetime import datetime
import subprocess
import importlib

# Import the AudioAnalyzer class
from audio_analyzer import AudioAnalyzer, find_duplicate_songs

class ToleranceDialog:
    """Dialog to get tolerance value for duplicate detection"""
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Duplicate Detection Settings")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create widgets
        ttk.Label(self.dialog, text="Tolerance in seconds:").pack(pady=(20, 5))
        
        self.tolerance_var = tk.StringVar(value="3.0")
        self.tolerance_entry = ttk.Entry(self.dialog, textvariable=self.tolerance_var, width=10)
        self.tolerance_entry.pack(pady=5)
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
    
    def on_ok(self):
        try:
            tolerance = float(self.tolerance_var.get())
            if tolerance <= 0:
                messagebox.showerror("Error", "Tolerance must be a positive number.")
                return
            
            self.result = tolerance
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")
    
    def on_cancel(self):
        self.dialog.destroy()
        
        
class AudioAnalyzerGUI:
    def check_mutagen(self):
        """Check if mutagen is installed and offer to install it"""
        try:
            import mutagen
            return True
        except ImportError:
            result = messagebox.askquestion("Install Required", 
                "The 'mutagen' library is required to edit audio file tags.\n"
                "Do you want to install it now?")
            
            if result == 'yes':
                try:
                    self.status_var.set("Installing mutagen...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "mutagen"])
                    self.status_var.set("Mutagen installed successfully")
                    import mutagen
                    return True
                except Exception as e:
                    messagebox.showerror("Installation Error", 
                        f"Failed to install mutagen: {str(e)}\n"
                        "Please install it manually with:\n"
                        "pip install mutagen")
                    return False
            return False
    
    def check_dependencies(self):
        """Check for all required dependencies"""
        missing = []
        
        # Check for required libraries
        try:
            import numpy
        except ImportError:
            missing.append("numpy")
        
        try:
            import matplotlib
        except ImportError:
            missing.append("matplotlib")
        
        try:
            import librosa
        except ImportError:
            missing.append("librosa")
        
        try:
            import pydub
        except ImportError:
            missing.append("pydub")
        
        # If there are missing dependencies, offer to install them
        if missing:
            result = messagebox.askquestion("Install Dependencies", 
                f"The following libraries are required but not installed:\n"
                f"{', '.join(missing)}\n\n"
                f"Do you want to install them now? This may take a few minutes.")
            
            if result == 'yes':
                try:
                    self.status_var.set(f"Installing dependencies: {', '.join(missing)}...")
                    
                    # Install each missing dependency
                    for lib in missing:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                    
                    # Force reload libraries
                    if 'numpy' in missing:
                        importlib.reload(numpy)
                    if 'matplotlib' in missing:
                        importlib.reload(matplotlib)
                    if 'librosa' in missing:
                        importlib.reload(librosa)
                    if 'pydub' in missing:
                        importlib.reload(pydub)
                    
                    self.status_var.set("Dependencies installed successfully")
                    
                except Exception as e:
                    messagebox.showerror("Installation Error", 
                        f"Failed to install dependencies: {str(e)}\n"
                        "Please install them manually with:\n"
                        f"pip install {' '.join(missing)}")
    
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Analyzer")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)
        
        # Dictionary to store analysis results
        self.analysis_