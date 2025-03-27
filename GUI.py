import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# Import required modules
from audio_analyzer import AudioAnalyzer, TraktorNMLEditor, find_duplicate_songs


class AudioAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Analyzer")
        self.root.geometry("1000x700")  # Larger window for the table
        
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
        
        self.save_button = ttk.Button(
            self.button_frame, 
            text="Save Changes", 
            command=self.save_changes,
            width=20,
            state=tk.DISABLED  # Initially disabled
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.find_duplicates_button = ttk.Button(
            self.button_frame, 
            text="Find Duplicate Files", 
            command=self.find_duplicates,
            width=20
        )
        self.find_duplicates_button.pack(side=tk.LEFT, padx=5)

        # Create table frame
        self.table_frame = ttk.Frame(self.main_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview (table)
        self.create_treeview()
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_treeview(self):
        # Scrollbar
        scrollbar_y = ttk.Scrollbar(self.table_frame, orient="vertical")
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(self.table_frame, orient="horizontal")
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create columns
        columns = ("filepath", "title", "bpm", "key", "key_text", "intro", "buildup", "drop")
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        
        # Configure scrollbars
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Define headings
        self.tree.heading("filepath", text="File Path")
        self.tree.heading("title", text="Title")
        self.tree.heading("bpm", text="BPM")
        self.tree.heading("key", text="Key")
        self.tree.heading("key_text", text="Key Text")
        self.tree.heading("intro", text="Intro (mm:ss)")
        self.tree.heading("buildup", text="Buildup (mm:ss)")
        self.tree.heading("drop", text="Drop (mm:ss)")
        
        # Define columns width
        self.tree.column("filepath", width=300)
        self.tree.column("title", width=150)
        self.tree.column("bpm", width=50)
        self.tree.column("key", width=50)
        self.tree.column("key_text", width=80)
        self.tree.column("intro", width=100)
        self.tree.column("buildup", width=100)
        self.tree.column("drop", width=100)
        
        # Pack treeview
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Enable editing on double-click
        self.tree.bind("<Double-1>", self.on_cell_double_click)
    
    def on_cell_double_click(self, event):
        """Handle double-click on a cell to edit the value"""
        # Get the item and column that was clicked
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        # Get column name
        column_index = int(column[1:]) - 1
        column_name = self.tree["columns"][column_index]
        
        # Don't allow editing filepath
        if column_name == "filepath":
            return
        
        # Get current value
        current_value = self.tree.set(item, column_name)
        
        # Create entry widget for editing
        x, y, width, height = self.tree.bbox(item, column)
        
        # Create an Entry widget
        entry = ttk.Entry(self.tree)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def on_entry_complete(event=None):
            # Update treeview with the new value
            self.tree.set(item, column_name, entry.get())
            
            # Update the data in our dictionary
            file_path = self.tree.set(item, "filepath")
            if file_path in self.analysis_results:
                # Handle CUE points specially
                if column_name in ["intro", "buildup", "drop"]:
                    time_str = entry.get()
                    try:
                        # Parse mm:ss format to seconds
                        parts = time_str.split(":")
                        if len(parts) == 2:
                            minutes = int(parts[0])
                            seconds = int(parts[1])
                            total_seconds = minutes * 60 + seconds
                            
                            # Update CUE points
                            cue_type = column_name
                            self.analysis_results[file_path]["cue_points"][cue_type] = total_seconds
                    except ValueError:
                        pass  # Ignore invalid format
                else:
                    # Update other fields directly
                    self.analysis_results[file_path][column_name] = entry.get()
            
            # Destroy the entry widget
            entry.destroy()
        
        # Bind Enter key to complete editing
        entry.bind("<Return>", on_entry_complete)
        entry.bind("<FocusOut>", on_entry_complete)
        
        # Place the entry widget
        entry.place(x=x, y=y, width=width, height=height)
    
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
            self.progress_var.set(0)
            
            # Clear the table
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Clear previous results
            self.analysis_results = {}
            
            for i, file_path in enumerate(file_paths):
                # Update progress
                progress = (i / len(file_paths)) * 100
                self.progress_var.set(progress)
                
                self.status_var.set(f"Analyzing file {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                
                # Perform analysis
                analyzer = AudioAnalyzer(file_path)
                bpm = analyzer.analyze_bpm()
                key = analyzer.analyze_key()
                
                # Detect CUE points
                cue_points = analyzer.detect_cue_points()
                
                # Format CUE points for display
                intro_time = self._format_time(cue_points.get('intro', 0))
                build_time = self._format_time(cue_points.get('build', 0))
                drop_time = self._format_time(cue_points.get('drop', 0))
                
                # Store results
                self.analysis_results[file_path] = {
                    'title': os.path.basename(file_path),
                    'bpm': bpm,
                    'key': analyzer.traktor_key,
                    'key_text': analyzer.traktor_key_text,
                    'cue_points': cue_points
                }
                
                # Add to table
                self.tree.insert(
                    "", 
                    tk.END, 
                    values=(
                        file_path,
                        os.path.basename(file_path),
                        f"{bpm:.1f}" if bpm else "",
                        analyzer.traktor_key,
                        analyzer.traktor_key_text,
                        intro_time,
                        build_time,
                        drop_time
                    )
                )
                
                # Update UI
                self.root.update_idletasks()
            
            # Complete the progress bar
            self.progress_var.set(100)
            self.status_var.set(f"Analysis complete. Analyzed {len(file_paths)} files.")
            
            # Enable save button
            self.save_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during analysis: {str(e)}")
    
    def save_changes(self):
        """Save tags to MP3 files and CUE points to Traktor"""
        if not self.analysis_results:
            messagebox.showinfo("Info", "No analysis results to save.")
            return
        
        try:
            self.status_var.set("Saving changes...")
            self.progress_var.set(0)
            
            # Try to import mutagen for MP3 tag editing
            try:
                import mutagen
                from mutagen.id3 import ID3, TIT2, TBPM, TKEY
                mutagen_available = True
            except ImportError:
                mutagen_available = False
                messagebox.showwarning("Warning", 
                                     "Mutagen library not found. MP3 tags will not be saved.\n"
                                     "Install mutagen with: pip install mutagen")
            
            # Locate Traktor collection file
            #traktor_dir = "C:\\Users\\home\\Documents\\Native Instruments\\Traktor 3.11.1"
            traktor_dir = "C:\\Users\\home\\Documents\\DJ\\DEV\\MusicAnalyzer"
            nml_path = os.path.join(traktor_dir, "collection.nml")
            
            if not os.path.exists(nml_path):
                messagebox.showwarning("Warning", 
                                     f"Traktor collection file not found at: {nml_path}\n"
                                     "CUE points will not be saved to Traktor.")
                traktor_available = False
            else:
                traktor_available = True
                editor = TraktorNMLEditor(nml_path)
                
            # Process each file
            total_files = len(self.analysis_results)
            saved_mp3_count = 0
            saved_traktor_count = 0
            
            for i, (file_path, data) in enumerate(self.analysis_results.items()):
                # Update progress
                progress = (i / total_files) * 100
                self.progress_var.set(progress)
                
                # Save MP3 tags if available
                if mutagen_available and file_path.lower().endswith('.mp3'):
                    try:
                        # Load ID3 tags
                        audio = ID3(file_path)
                        
                        # Update tags
                        if data.get('title'):
                            audio["TIT2"] = TIT2(encoding=3, text=data['title'])
                        
                        if data.get('bpm'):
                            bpm_str = str(int(float(data['bpm'])))
                            audio["TBPM"] = TBPM(encoding=3, text=bpm_str)
                        
                        if data.get('key'):
                            audio["TKEY"] = TKEY(encoding=3, text=data['key'])
                        
                        # Save changes
                        audio.save()
                        saved_mp3_count += 1
                        
                    except Exception as e:
                        print(f"Error saving MP3 tags for {file_path}: {e}")
                
                # Save CUE points to Traktor if available
                if traktor_available and 'cue_points' in data and data['cue_points']:
                    try:
                        # Define custom names for the CUE points
                        cue_names = {
                            'intro': "INTRO",
                            'build': "BUILD",
                            'drop': "DROP",
                            'outro': "OUTRO"
                        }
                        
                        # Add the CUE points to the NML file
                        success = editor.add_cue_points(file_path, data['cue_points'], cue_names)
                        if success:
                            saved_traktor_count += 1
                            
                    except Exception as e:
                        print(f"Error saving CUE points for {file_path}: {e}")
            
            # Complete the progress bar
            self.progress_var.set(100)
            
            # Show completion message
            messagebox.showinfo("Save Complete", 
                               f"Changes saved:\n"
                               f"- MP3 tags: {saved_mp3_count} files\n"
                               f"- Traktor CUE points: {saved_traktor_count} files")
            
            self.status_var.set("Save completed.")
            
        except Exception as e:
            self.status_var.set(f"Error saving changes: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while saving changes: {str(e)}")
    
    def _format_time(self, seconds):
        """Format seconds as mm:ss"""
        if not seconds:
            return "00:00"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


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
            from audio_analyzer import find_duplicate_songs
            self.status_var.set(f"Scanning directory for duplicates: {directory}")
            self.progress_var.set(0)
            
            # Clear the table
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Print initial message to the status
            self.status_var.set("Scanning for duplicates. This may take a while...")
            
            # Find duplicates with progress callback
            def update_progress(value):
                self.progress_var.set(value)
                self.root.update_idletasks()
            
            duplicates = find_duplicate_songs(directory, tolerance_sec, self.progress_var.set)
            
            # Clear the table for fresh results
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Display only duplicate results
            if duplicates:
                for i, group in enumerate(duplicates):
                    # Use a tag to color each group differently
                    tag_name = f"group{i}"
                    self.tree.tag_configure(tag_name, background=f"#{'%02x' % ((i*30) % 256)}{'%02x' % ((i*50) % 256)}ff")
                    
                    for j, file_path in enumerate(group):
                        filename = os.path.basename(file_path)
                        
                        # For duplicate files, we'll only show basic info
                        self.tree.insert(
                            "", 
                            tk.END, 
                            values=(file_path, filename, "", "", "", "", "", ""),
                            tags=(tag_name,)
                        )
                
                self.status_var.set(f"Found {len(duplicates)} groups of duplicate files.")
            else:
                self.status_var.set("No duplicate files found.")
                messagebox.showinfo("Results", "No duplicate files found.")
            
            # Update progress bar to complete
            self.progress_var.set(100)
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during duplicate search: {str(e)}")





# Function to capture print statements
def write(self, text):
    self.output_text.insert(tk.END, text)
    self.output_text.see(tk.END)

def flush(self):
    pass  # Needed for stdout compatibility

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    app = AudioAnalyzerGUI(root)
    
    # Run the application
    root.mainloop()