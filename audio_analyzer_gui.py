import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# Import the AudioAnalyzer class
from audio_analyzer import AudioAnalyzer, find_duplicate_songs

class SimpleAudioAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Analyzer")
        self.root.geometry("800x600")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Add buttons
        self.analyze_button = ttk.Button(
            self.button_frame, 
            text="Analyze Files", 
            command=self.analyze_files,
            width=20
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.find_duplicates_button = ttk.Button(
            self.button_frame, 
            text="Find Duplicate Files", 
            command=self.find_duplicates,
            width=20
        )
        self.find_duplicates_button.pack(side=tk.LEFT, padx=5)
        
        # Create text output area
        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.output_text = tk.Text(self.output_frame, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def analyze_files(self):
        """Analyze multiple audio files"""
        file_paths = filedialog.askopenfilenames(
            title="Select audio files to analyze",
            filetypes=(
                ("Audio files", "*.mp3 *.wav *.flac *.aac *.m4a *.ogg"),
                ("All files", "*.*")
            )
        )
        
        if not file_paths:
            return
        
        # Start analysis in a separate thread
        threading.Thread(target=self._analyze_files_thread, args=(file_paths,), daemon=True).start()
    
    def _analyze_files_thread(self, file_paths):
        """Thread function to analyze files without blocking the GUI"""
        try:
            self.status_var.set("Analyzing files...")
            self.output_text.delete(1.0, tk.END)
            
            for i, file_path in enumerate(file_paths):
                # Update progress
                progress = (i / len(file_paths)) * 100
                self.progress_var.set(progress)
                
                self.status_var.set(f"Analyzing file {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                
                # Redirect print output to our text widget
                old_stdout = sys.stdout
                sys.stdout = self
                
                # Perform analysis
                analyzer = AudioAnalyzer(file_path)
                bpm = analyzer.analyze_bpm()
                key = analyzer.analyze_key()
                
                # Return to normal stdout
                sys.stdout = old_stdout
                
                self.output_text.see(tk.END)
                self.root.update_idletasks()
            
            # Complete the progress bar
            self.progress_var.set(100)
            self.status_var.set(f"Analysis complete. Analyzed {len(file_paths)} files.")
            
            # Show completion message
            messagebox.showinfo("Analysis Complete", f"Successfully analyzed {len(file_paths)} files.")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during analysis: {str(e)}")
    
    def find_duplicates(self):
        """Find duplicate audio files"""
        directory = filedialog.askdirectory(title="Select directory to scan for duplicates")
        
        if not directory:
            return
        
        # Get tolerance value
        tolerance_sec = 3.0  # Default
        
        # Start duplicate search in a separate thread
        threading.Thread(target=self._find_duplicates_thread, args=(directory, tolerance_sec), daemon=True).start()
    
    def _find_duplicates_thread(self, directory, tolerance_sec):
        """Thread function to find duplicates without blocking the GUI"""
        try:
            self.status_var.set(f"Scanning directory for duplicates: {directory}")
            self.output_text.delete(1.0, tk.END)
            self.progress_var.set(0)
            
            # Print initial message to the text area
            self.output_text.insert(tk.END, "Scanning for duplicates. This may take a while...\n")
            self.output_text.insert(tk.END, "Please wait while scanning files. Results will appear here.\n\n")
            self.output_text.see(tk.END)
            
            # Completely suppress normal stdout during scanning
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')  # Redirect to null device
            
            # Find duplicates with progress callback
            duplicates = find_duplicate_songs(directory, tolerance_sec, self.update_progress)
            
            # Restore stdout
            sys.stdout.close()
            sys.stdout = old_stdout
            
            # Clear the text area for fresh results
            self.output_text.delete(1.0, tk.END)
            
            # Display only duplicate results
            if duplicates:
                self.output_text.insert(tk.END, f"Found {len(duplicates)} groups of duplicate files.\n\n")
                
                for i, group in enumerate(duplicates):
                    self.output_text.insert(tk.END, f"Group {i+1}:\n")
                    
                    for j, file_path in enumerate(group):
                        filename = os.path.basename(file_path)
                        self.output_text.insert(tk.END, f"  {j+1}. {filename}\n")
                        self.output_text.insert(tk.END, f"     Path: {file_path}\n")
                    
                    self.output_text.insert(tk.END, "\n")
            else:
                self.output_text.insert(tk.END, "No duplicate files found.\n")
            
            # Update progress bar to complete
            self.progress_var.set(100)
            
            # Update status
            result_message = f"Found {len(duplicates)} groups of duplicate files." if duplicates else "No duplicates found."
            self.status_var.set(result_message)
            
            # Show completion message
            messagebox.showinfo("Duplicate Search Complete", result_message)
            
        except Exception as e:
            # Make sure to restore stdout in case of error
            if sys.stdout != old_stdout:
                sys.stdout.close()
                sys.stdout = old_stdout
                
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during duplicate search: {str(e)}")
    # Function to capture print statements
    def write(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
    
    def flush(self):
        pass  # Needed for stdout compatibility

    # Custom method to update progress bar from the find_duplicates function
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    app = SimpleAudioAnalyzerGUI(root)
    
    # Run the application
    root.mainloop()