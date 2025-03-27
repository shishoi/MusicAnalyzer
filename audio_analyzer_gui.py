import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# Import the AudioAnalyzer class
from audio_analyzer import AudioAnalyzer, TraktorNMLEditor, find_duplicate_songs

class SimpleAudioAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Analyzer")
        self.root.geometry("900x700")  # Slightly larger window for additional controls
        
        # Dictionary to store analysis results
        self.analysis_results = {}
        
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
        
        self.save_cues_button = ttk.Button(
            self.button_frame, 
            text="Save CUEs to Traktor", 
            command=self.save_cues_to_traktor,
            width=20,
            state=tk.DISABLED  # Initially disabled until we have analysis results
        )
        self.save_cues_button.pack(side=tk.LEFT, padx=5)
        
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
                # Initialize or clear the analysis results
                self.analysis_results = {}
                
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
                    
                    # Detect CUE points
                    print("\nDetecting CUE points...")
                    cue_points = analyzer.detect_cue_points()
                    
                    # Store results
                    self.analysis_results[file_path] = {
                        'bpm': bpm,
                        'key': key, 
                        'traktor_key': analyzer.traktor_key,
                        'traktor_key_text': analyzer.traktor_key_text,
                        'cue_points': cue_points
                    }
                    
                    # Return to normal stdout
                    sys.stdout = old_stdout
                    
                    # Add a visual separator
                    self.output_text.insert(tk.END, f"\n{'='*50}\n")
                    
                    self.output_text.see(tk.END)
                    self.root.update_idletasks()
                
                # Complete the progress bar
                self.progress_var.set(100)
                self.status_var.set(f"Analysis complete. Analyzed {len(file_paths)} files.")
                
                # Enable the save button if we have results
                if self.analysis_results:
                    self.save_cues_button.config(state=tk.NORMAL)
                
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




        def save_cues_to_traktor(self):
            """Save detected CUE points to Traktor collection.nml"""
            if not hasattr(self, 'analysis_results') or not self.analysis_results:
                messagebox.showinfo("Info", "No analysis results available. Analyze files first.")
                return
            
            # Create a new window to select which file to save CUEs for
            file_selection_window = tk.Toplevel(self.root)
            file_selection_window.title("Select File to Save CUEs")
            file_selection_window.geometry("600x400")
            file_selection_window.grab_set()  # Make window modal
            
            # Instructions
            ttk.Label(file_selection_window, text="Select the file you want to save CUE points for:", padding=10).pack(anchor=tk.W)
            
            # Create a frame for the listbox and scrollbar
            list_frame = ttk.Frame(file_selection_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create listbox
            file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
            file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=file_listbox.yview)
            
            # Populate listbox with analyzed files
            for file_path in self.analysis_results.keys():
                file_listbox.insert(tk.END, os.path.basename(file_path))
            
            # Add selection buttons
            button_frame = ttk.Frame(file_selection_window)
            button_frame.pack(fill=tk.X, pady=10)
            
            def on_save_selected():
                selection = file_listbox.curselection()
                if not selection:
                    messagebox.showinfo("Info", "Please select a file first.")
                    return
                    
                # Get the selected file path
                selected_index = selection[0]
                selected_file = list(self.analysis_results.keys())[selected_index]
                
                # Close the selection window
                file_selection_window.destroy()
                
                # Save the CUEs to Traktor
                self._save_cues_for_file(selected_file)

                ttk.Button(button_frame, text="Save CUEs", command=on_save_selected).pack(side=tk.RIGHT, padx=10)
                ttk.Button(button_frame, text="Cancel", command=file_selection_window.destroy).pack(side=tk.RIGHT, padx=5)
                
                # Show preview of CUE points for the selected file
                preview_frame = ttk.LabelFrame(file_selection_window, text="CUE Points Preview")
                preview_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
                
                preview_text = tk.Text(preview_frame, height=8, wrap=tk.WORD)
                preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
                def on_file_select(event):
                    selection = file_listbox.curselection()
                    if not selection:
                        return
                        
                    # Clear preview
                    preview_text.delete(1.0, tk.END)
                    
                    # Get the selected file path
                    selected_index = selection[0]
                    selected_file = list(self.analysis_results.keys())[selected_index]
                    
                    # Show CUE points
                    cue_points = self.analysis_results[selected_file]['cue_points']
                    if cue_points:
                        for cue_type, time in cue_points.items():
                            minutes = int(time // 60)
                            seconds = int(time % 60)
                            preview_text.insert(tk.END, f"{cue_type.capitalize()}: {minutes:02d}:{seconds:02d}\n")
                    else:
                        preview_text.insert(tk.END, "No CUE points detected for this file.")
                    
                # Bind selection event
                file_listbox.bind('<<ListboxSelect>>', on_file_select)

            def _save_cues_for_file(self, file_path):
                """Save CUE points for a specific file to Traktor"""
            try:
                # Get the CUE points
                cue_points = self.analysis_results[file_path]['cue_points']
                
                if not cue_points:
                    messagebox.showinfo("Info", "No CUE points detected for this file.")
                    return
            

                # Locate Traktor collection file
                traktor_dir = "C:\\Users\\home\\Documents\\Native Instruments\\Traktor 3.11.1"
                nml_path = os.path.join(traktor_dir, "collection.nml")
                
                if not os.path.exists(nml_path):
                    messagebox.showerror("Error", f"Traktor collection file not found at: {nml_path}")
                    return
                
                # Create NML editor and save CUE points
                editor = TraktorNMLEditor(nml_path)
                
                # Define custom names for the CUE points
                cue_names = {
                    'intro': "INTRO",
                    'build': "BUILD",
                    'drop': "DROP",
                    'outro': "OUTRO"
                }
                
                # Add the CUE points to the NML file
                success = editor.add_cue_points(file_path, cue_points, cue_names)
                
                if success:
                    messagebox.showinfo("Success", 
                                        f"CUE points successfully added to Traktor collection for:\n"
                                        f"{os.path.basename(file_path)}")
                    
                    # Show instructions for Traktor
                    messagebox.showinfo("Next Steps", 
                                        "To use these CUE points in Traktor:\n\n"
                                        "1. Open Traktor Pro\n"
                                        "2. Your CUE points should now be available as HOT CUES\n"
                                        "3. If they don't appear, try refreshing the collection in Traktor")
                else:
                    messagebox.showerror("Error", "Failed to save CUE points to Traktor collection")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving CUE points to Traktor: {str(e)}")

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