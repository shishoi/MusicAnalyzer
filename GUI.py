import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess

# Import required modules
from audio_analyzer import AudioAnalyzer, TraktorNMLEditor, find_duplicate_songs, load_collection_path, save_collection_path, parse_traktor_collection

# Optional: VLC-based playback support (python-vlc)
try:
    import vlc
    _vlc_available = True
except Exception:
    vlc = None
    _vlc_available = False


class ToolTip:
    """Simple tooltip class for tkinter widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        widget.bind("<Enter>", self.showtip, add="+")
        widget.bind("<Leave>", self.hidetip, add="+")

    def showtip(self, event=None):
        """Display the tooltip."""
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 50
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("tahoma", 9, "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        """Hide the tooltip."""
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class AudioAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Analyzer")
        self.root.geometry("1000x700")  # Larger window for the table
        
        # Dictionary to store analysis results
        self.analysis_results = {}
        
        # Track current mode: 'analyze' or 'duplicates'
        self.current_mode = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Add buttons (reordered and renamed)
        # 1. Find Duplicates
        self.find_duplicates_button = ttk.Button(
            self.button_frame, 
            text="🗐 Find Duplicates", 
            command=self.find_duplicates,
            width=20
        )
        self.find_duplicates_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.find_duplicates_button, 
                "Detect duplicate audio files using intelligent scoring:\n"
                "• Filename Similarity (50%)\n"
                "• Album Match (15%)\n"
                "• Artist Match (15%)\n"
                "• File Size (10%)\n"
                "• Duration (10%)\n"
                "• Title Match (10%)\n"
                "Groups ranked by confidence score.")
        
        # 2. Rename Files (placeholder)
        self.rename_files_button = ttk.Button(
            self.button_frame,
            text="📝 Rename Files",
            command=self.rename_files,
            width=20,
            state=tk.DISABLED  # Will enable when rename feature is implemented
        )
        self.rename_files_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.rename_files_button,
                "Remove illegal characters from filenames/titles to prevent software crashes")

        # 3. Quality Check
        self.quality_check_button = ttk.Button(
            self.button_frame,
            text="✓ Quality Check",
            command=self.quality_check,
            width=20
        )
        self.quality_check_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.quality_check_button,
                "Check audio quality: bitrate, sample rate, format, missing metadata")

        # 4. My Collection
        self.collection_button = ttk.Button(
            self.button_frame,
            text="🎵 My Collection",
            command=self.analyze_collection,
            width=20
        )
        self.collection_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.collection_button,
                "Display and analyze your DJ collection (Traktor/Recordbox/Serato)")
        
        # 5. Analyze Files
        self.analyze_button = ttk.Button(
            self.button_frame, 
            text="🔍 Analyze Files", 
            command=self.analyze_files,
            width=20
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.analyze_button,
                "Analyze audio files: BPM detection, key analysis, CUE point detection")
        
        # 6. Save Changes
        self.save_button = ttk.Button(
            self.button_frame, 
            text="💾 Save Changes", 
            command=self.save_changes,
            width=20,
            state=tk.DISABLED  # Initially disabled
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.save_button, 
                "Save analysis results:\n- MP3 tags: Title, BPM, Key\n- Traktor CUE points: Intro, Build, Drop, Outro")
        
        # 7. Delete Selected
        self.delete_selected_button = ttk.Button(
            self.button_frame,
            text="🗑️ Delete Selected",
            command=self.delete_selected_files,
            width=20,
            state=tk.DISABLED
        )
        self.delete_selected_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.delete_selected_button,
                "Delete selected files to Recycle Bin")

        # Initialize playback controls and VLC player (if available)
        try:
            self._init_playback_controls()
        except Exception:
            pass

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Create table frame
        self.table_frame = ttk.Frame(self.main_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview (table)
        self.create_treeview()
        
        # Bottom area: feedback (left) and status bar (right)
        self.bottom_frame = ttk.Frame(root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.feedback_var = tk.StringVar()
        self.feedback_var.set("")
        self.feedback_label = ttk.Label(self.bottom_frame, textvariable=self.feedback_var, anchor=tk.W)
        self.feedback_label.pack(side=tk.LEFT, fill=tk.X, padx=6)

        # Status bar (right)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.RIGHT, fill=tk.X)

        # Feedback animation handle
        self._feedback_after_id = None
        self._feedback_base = ""
        self._feedback_dots = 0

        # VLC player setup
        self.vlc_available = _vlc_available
        if self.vlc_available:
            try:
                self.vlc_instance = vlc.Instance()
                self.vlc_player = self.vlc_instance.media_player_new()
            except Exception:
                self.vlc_available = False
                self.vlc_instance = None
                self.vlc_player = None
        else:
            self.vlc_instance = None
            self.vlc_player = None

        # Store parsed collection tracks and cover image refs
        self.collection_tracks = {}
        self._cover_images = {}

    def create_treeview(self):
        # Scrollbar
        scrollbar_y = ttk.Scrollbar(self.table_frame, orient="vertical")
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(self.table_frame, orient="horizontal")
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Columns for "Analyze Files" mode
        self.analyze_columns = ("filepath", "orig_bpm", "analyzed_bpm", "key", "traktor_key", "intro", "build", "drop", "outro")
        
        # Columns for "Find Duplicates" mode
        self.duplicates_columns = ("filepath", "title", "artists", "album", "bitrate", "length", "size_mb", "BPM", "year", "has_cover")
        
        # Start with duplicates columns (neutral default)
        columns = self.duplicates_columns
        
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        
        # Configure scrollbars
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Define headings for duplicates mode (will be overridden when switching modes)

        self._setup_duplicates_columns()
        
        # Pack treeview
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Enable editing on double-click
        self.tree.bind("<Double-1>", self.on_cell_double_click)
        # Bind Delete key to deletion handler
        self.tree.bind("<Delete>", lambda e: self.delete_selected_files())
        # Bind right-click to context menu
        self.tree.bind("<Button-3>", self._on_tree_right_click)
    
    def _setup_analyze_columns(self):
        """Set up columns for Analyze Files mode."""
        # Remove existing columns
        for col in self.tree["columns"]:
            self.tree.column(col, width=0, stretch=tk.NO)
        
        # Reconfigure with analyze columns
        self.tree.configure(columns=self.analyze_columns)
        
        # Define headings
        self.tree.heading("filepath", text="File Path")
        self.tree.heading("orig_bpm", text="Original BPM")
        self.tree.heading("analyzed_bpm", text="Analyzed BPM")
        self.tree.heading("key", text="KEY")
        self.tree.heading("traktor_key", text="TRAKTOR KEY")
        self.tree.heading("intro", text="Intro")
        self.tree.heading("build", text="Build")
        self.tree.heading("drop", text="Drop")
        self.tree.heading("outro", text="Outro")
        
        # Define columns width
        self.tree.column("filepath", width=400)
        self.tree.column("orig_bpm", width=100)
        self.tree.column("analyzed_bpm", width=100)
        self.tree.column("key", width=80)
        self.tree.column("traktor_key", width=100)
        self.tree.column("intro", width=80)
        self.tree.column("build", width=80)
        self.tree.column("drop", width=80)
        self.tree.column("outro", width=80)
    
    def _setup_duplicates_columns(self):
        """Set up columns for Find Duplicates mode."""
        # Remove existing columns
        for col in self.tree["columns"]:
            self.tree.column(col, width=0, stretch=tk.NO)
        
        # Reconfigure with duplicates columns
        self.tree.configure(columns=self.duplicates_columns)
        
        # Define headings
        self.tree.heading("filepath", text="File Path")
        self.tree.heading("title", text="Title")
        self.tree.heading("artists", text="Contributing Artists")
        self.tree.heading("album", text="Album")
        self.tree.heading("bitrate", text="Bit Rate")
        self.tree.heading("length", text="Length")
        self.tree.heading("size_mb", text="Size (MB)")
        self.tree.heading("BPM", text="BPM")
        self.tree.heading("year", text="Year")
        self.tree.heading("has_cover", text="Cover")
        
        # Define columns width
        self.tree.column("filepath", width=450)
        self.tree.column("title", width=250)
        self.tree.column("artists", width=180)
        self.tree.column("album", width=200)
        self.tree.column("bitrate", width=30)
        self.tree.column("length", width=30)
        self.tree.column("size_mb", width=30)
        self.tree.column("BPM", width=30)
        self.tree.column("year", width=30)
        self.tree.column("has_cover", width=40)
    
    def _setup_collection_columns(self):
        """Set up columns for Collection Analysis mode."""
        # Remove existing columns
        for col in self.tree["columns"]:
            self.tree.column(col, width=0, stretch=tk.NO)
        
        # Comprehensive collection columns
        self.collection_columns = (
            "filepath", "title", "artist", "remixer", "producer", "album", "genre",
            "label", "catalogno", "release_date", "track_number", "bpm", "key", "key_text",
            "bitrate", "length", "autogain", "rating", "mix", "comment", "lyrics", "cover"
        )
        
        # Reconfigure with collection columns
        self.tree.configure(columns=self.collection_columns)
        
        # Define headings
        self.tree.heading("filepath", text="File Path")
        self.tree.heading("title", text="Title")
        self.tree.heading("artist", text="Artist")
        self.tree.heading("remixer", text="Remixer")
        self.tree.heading("producer", text="Producer")
        self.tree.heading("album", text="Album")
        self.tree.heading("genre", text="Genre")
        self.tree.heading("label", text="Label")
        self.tree.heading("catalogno", text="Cat. No.")
        self.tree.heading("release_date", text="Release Date")
        self.tree.heading("track_number", text="Track No.")
        self.tree.heading("bpm", text="BPM")
        self.tree.heading("key", text="Key")
        self.tree.heading("key_text", text="Key Text")
        self.tree.heading("bitrate", text="Bitrate")
        self.tree.heading("length", text="Length")
        self.tree.heading("autogain", text="AutoGain")
        self.tree.heading("rating", text="Rating")
        self.tree.heading("mix", text="Mix")
        self.tree.heading("comment", text="Comment")
        self.tree.heading("lyrics", text="Lyrics")
        self.tree.heading("cover", text="Cover")
        
        # Define columns width
        self.tree.column("filepath", width=250)
        self.tree.column("title", width=250)
        self.tree.column("artist", width=200)
        self.tree.column("remixer", width=100)
        self.tree.column("producer", width=100)
        self.tree.column("album", width=120)
        self.tree.column("genre", width=80)
        self.tree.column("label", width=100)
        self.tree.column("catalogno", width=80)
        self.tree.column("release_date", width=80)
        self.tree.column("track_number", width=20)
        self.tree.column("bpm", width=30)
        self.tree.column("key", width=30)
        self.tree.column("key_text", width=250)
        self.tree.column("bitrate", width=30)
        self.tree.column("length", width=60)
        self.tree.column("autogain", width=70)
        self.tree.column("rating", width=50)
        self.tree.column("mix", width=80)
        self.tree.column("comment", width=150)
        self.tree.column("lyrics", width=100)
        self.tree.column("cover", width=50)
        
        # Bind column header clicks for sorting
        self.tree.bind("<Button-1>", self._on_collection_column_click)
        
        # Store sort state
        self.sort_column = None
        self.sort_reverse = False
    
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
        # If filepath column clicked, open in Explorer
        if column_name == "filepath":
            path = self.tree.set(item, "filepath")
            if path:
                self._open_in_explorer(path)
            return

        # If cover column clicked, show cover popup if available
        if column_name == "cover":
            filepath = self.tree.set(item, "filepath")
            track = self.collection_tracks.get(filepath, {})
            cover_path = track.get('cover_path') if track else None
            if cover_path:
                self._show_cover_popup(cover_path)
            else:
                messagebox.showinfo("Cover Art", "No cover art available for this track.")
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
        # Disable delete while analyzing
        try:
            self.delete_selected_button.config(state=tk.DISABLED)
        except Exception:
            pass
        # Start analysis in a separate thread
        threading.Thread(target=self._analyze_files_thread, args=(file_paths,), daemon=True).start()
    
    def _analyze_files_thread(self, file_paths):
        """Thread function to analyze files without blocking the GUI"""
        try:
            # Start animated feedback and status
            try:
                self.start_feedback("Analyzing files")
            except Exception:
                pass
            self.status_var.set("Analyzing files...")
            self.progress_var.set(0)
            
            # Switch to analyze mode columns
            self.current_mode = 'analyze'
            self._setup_analyze_columns()
            
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
                outro_time = self._format_time(cue_points.get('outro', 0))
                
                # Get original BPM from file tags
                meta = self._get_file_metadata(file_path)
                orig_bpm = meta.get('bpm') or ""
                
                # Store results (keep minimal structured data)
                self.analysis_results[file_path] = {
                    'title': os.path.basename(file_path),
                    'bpm': bpm,
                    'key': key,
                    'traktor_key': analyzer.traktor_key,
                    'traktor_key_text': analyzer.traktor_key_text,
                    'cue_points': cue_points
                }

                # Add to table: filepath, orig_bpm, analyzed_bpm, key, traktor_key, intro, build, drop, outro
                self.tree.insert(
                    "", 
                    tk.END, 
                    values=(
                        file_path,
                        orig_bpm,
                        f"{bpm:.1f}" if bpm else "",
                        key or "",
                        analyzer.traktor_key_text or "",
                        intro_time,
                        build_time,
                        drop_time,
                        outro_time
                    )
                )
                
                # Update UI
                self.root.update_idletasks()
            
            # Complete the progress bar
            self.progress_var.set(100)
            self.status_var.set(f"Analysis complete. Analyzed {len(file_paths)} files.")
            try:
                self.stop_feedback("Complete")
            except Exception:
                pass

            # Enable save button
            self.save_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            try:
                self.stop_feedback("Error")
            except Exception:
                pass
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


    def _get_file_metadata(self, file_path):
        """Return metadata for a file: title, bitrate (e.g. '320 kbps'), length (mm:ss), size_mb (string), artists, album, bpm, year, has_cover."""
        meta = {
            'title': None,
            'bitrate': None,
            'length': None,
            'size_mb': None,
            'artists': None,
            'album': None,
            'bpm': None,
            'year': None,
            'has_cover': 0
        }

        # Size in MB with 2 decimals
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            meta['size_mb'] = f"{size_mb:.2f}"
        except Exception:
            meta['size_mb'] = ""

        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(file_path, easy=True)
            info = None
            try:
                info = MutagenFile(file_path)
            except Exception:
                info = None

            # Title
            if audio is not None:
                title = None
                if 'title' in audio:
                    try:
                        title = audio.get('title')[0]
                    except Exception:
                        title = None
                meta['title'] = title

                # Artists
                artists = None
                if 'artist' in audio:
                    try:
                        artists = ", ".join(audio.get('artist'))
                    except Exception:
                        artists = None
                meta['artists'] = artists

                # Album
                album = None
                if 'album' in audio:
                    try:
                        album = audio.get('album')[0]
                    except Exception:
                        album = None
                meta['album'] = album

                # Year
                year = None
                if 'date' in audio:
                    try:
                        year = audio.get('date')[0]
                    except Exception:
                        year = None
                meta['year'] = year

            # Length and bitrate from info (non-easy Mutagen)
            if info is not None and hasattr(info, 'info') and info.info is not None:
                try:
                    length = int(info.info.length)
                    meta['length'] = self._format_time(length)
                except Exception:
                    meta['length'] = None

                # bitrate in bps -> convert to kbps
                try:
                    bitrate = getattr(info.info, 'bitrate', None)
                    if bitrate:
                        kbps = int(bitrate / 1000)
                        meta['bitrate'] = f"{kbps} kbps"
                except Exception:
                    meta['bitrate'] = None

            # Try to read TBPM (BPM) tag from easy tags if present
            try:
                if audio is not None and 'bpm' in audio:
                    meta['bpm'] = audio.get('bpm')[0]
                elif audio is not None and 'TBPM' in audio:
                    meta['bpm'] = audio.get('TBPM')[0]
            except Exception:
                pass

            # Check for cover art
            try:
                meta['has_cover'] = 0
                if info is not None:
                    has_picture = False
                    # Branch by container type to avoid false positives
                    info_type = type(info).__name__
                    # MP3: require APIC frame with real image mime and data
                    if info_type in ('MP3', 'EasyMP3') or 'mp3' in str(info.__class__).lower():
                        if hasattr(info, 'tags') and info.tags is not None:
                            allowed_mimes = {'image/jpeg', 'image/jpg', 'image/png'}
                            def looks_like_image(data_bytes: bytes) -> bool:
                                try:
                                    # JPEG starts with 0xFF 0xD8 and ends with 0xFF 0xD9
                                    if len(data_bytes) >= 4 and data_bytes[:2] == b"\xFF\xD8":
                                        return True
                                    # PNG starts with 89 50 4E 47 0D 0A 1A 0A
                                    if len(data_bytes) >= 8 and data_bytes[:8] == b"\x89PNG\r\n\x1a\n":
                                        return True
                                except Exception:
                                    return False
                                return False
                            for key, frame in info.tags.items():
                                if 'APIC' in key:
                                    mime = (getattr(frame, 'mime', '') or '').lower()
                                    data = getattr(frame, 'data', b'') or b''
                                    # Count any valid embedded image (not only FrontCover)
                                    if (mime in allowed_mimes) and len(data) >= 1024 and looks_like_image(data):
                                        has_picture = True
                                        break
                    # FLAC/OGG: metadata_block_picture present
                    elif info_type in ('FLAC', 'OggVorbis') or str(info.__class__).find('flac') != -1 or str(info.__class__).find('ogg') != -1:
                        has_picture = ('metadata_block_picture' in info)
                    # MP4/M4A: covr atom present
                    elif info_type in ('MP4',) or str(info.__class__).find('mp4') != -1:
                        has_picture = ('covr' in info)
                    meta['has_cover'] = 1 if has_picture else 0
            except Exception:
                meta['has_cover'] = 0

        except ImportError:
            # mutagen not available — set some defaults
            meta['title'] = os.path.basename(file_path)
        except Exception:
            # Any parsing error — be forgiving
            if not meta.get('title'):
                meta['title'] = os.path.basename(file_path)

        # Ensure fields are strings (not None)
        for k in list(meta.keys()):
            if meta[k] is None:
                meta[k] = ""

        return meta


    def _init_playback_controls(self):
        """Create single playback control area below main buttons, above table."""
        self.playback_frame = ttk.Frame(self.main_frame)
        self.playback_frame.pack(fill=tk.X, pady=5)

        # Button row (Play, Pause, Stop + slider)
        button_row = ttk.Frame(self.playback_frame)
        button_row.pack(fill=tk.X)

        self.play_pos_var = tk.DoubleVar()
        self.play_time_var = tk.StringVar(value="00:00/00:00")
        self._seeking = False

        self.play_button = ttk.Button(button_row, text="Play", command=self.play_selected_file)
        self.play_button.pack(side=tk.LEFT, padx=2)
        self.play_button.config(text="▶️ Play")
        self.pause_button = ttk.Button(button_row, text="Pause", command=self.pause_playback)
        self.pause_button.pack(side=tk.LEFT, padx=2)
        self.pause_button.config(text="⏸️ Pause")
        self.stop_button = ttk.Button(button_row, text="Stop", command=self.stop_playback)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        self.stop_button.config(text="⏹️ Stop")

        self.pos_scale = ttk.Scale(button_row, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.play_pos_var, command=self._on_seek)
        self.pos_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        self.time_label = ttk.Label(button_row, textvariable=self.play_time_var)
        self.time_label.pack(side=tk.LEFT, padx=5)

        # Song name label row (below buttons)
        label_row = ttk.Frame(self.playback_frame)
        label_row.pack(fill=tk.X, pady=2)

        self.play_label = ttk.Label(label_row, text="No track selected", font=("Arial", 10, "bold"))
        self.play_label.pack(side=tk.LEFT, padx=5)

        # Disable controls if VLC not available; will be enabled if available
        if not _vlc_available:
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)

    # --- Feedback animation helpers ---
    def _feedback_tick(self):
        """Internal: update animated dots"""
        self._feedback_dots = (self._feedback_dots + 1) % 4
        dots = '.' * self._feedback_dots
        self.feedback_var.set(self._feedback_base + dots)
        self._feedback_after_id = self.root.after(500, self._feedback_tick)

    def start_feedback(self, text):
        """Start animated feedback with base text (e.g. 'Analyzing')."""
        # Stop existing animation
        try:
            if self._feedback_after_id:
                self.root.after_cancel(self._feedback_after_id)
        except Exception:
            pass
        self._feedback_base = text
        self._feedback_dots = 0
        self.feedback_var.set(text)
        self._feedback_after_id = self.root.after(500, self._feedback_tick)

    def stop_feedback(self, final_text=None, timeout_clear=3000):
        """Stop animation and show final_text (or 'Complete'). Clears after timeout_clear ms if provided."""
        try:
            if self._feedback_after_id:
                self.root.after_cancel(self._feedback_after_id)
        except Exception:
            pass
        self._feedback_after_id = None
        msg = final_text or "Complete"
        self.feedback_var.set(msg)
        # Optionally clear after a few seconds
        if timeout_clear:
            def _clear():
                try:
                    self.feedback_var.set("")
                except Exception:
                    pass
            self.root.after(timeout_clear, _clear)

    def play_selected_file(self):
        """Play the currently selected file in the treeview."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "No file selected to play.")
            return
        path = self.tree.set(sel[0], "filepath")
        if not path:
            messagebox.showinfo("Info", "Selected row has no file path.")
            return
        
        # Normalize path
        path = os.path.normpath(path)
        
        # Verify file exists
        if not os.path.exists(path) or not os.path.isfile(path):
            messagebox.showerror("File Error", f"File not found or is not a file:\n{path}")
            return
        
        self.play_label.config(text=os.path.basename(path))
        if not self.vlc_available or self.vlc_player is None:
            messagebox.showwarning("Playback unavailable", "python-vlc is not available. Install 'python-vlc' and ensure VLC/libvlc is installed on your system.")
            return
        try:
            media = self.vlc_instance.media_new(path)
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            # start updating position
            self._update_playback_position()
        except Exception as e:
            messagebox.showerror("Playback Error", f"Failed to play file: {e}")

    def pause_playback(self):
        if not self.vlc_available or self.vlc_player is None:
            return
        try:
            self.vlc_player.pause()
        except Exception:
            pass

    def stop_playback(self):
        if not self.vlc_available or self.vlc_player is None:
            return
        try:
            self.vlc_player.stop()
            self.play_pos_var.set(0)
            self.play_time_var.set("00:00/00:00")
        except Exception:
            pass

    def _on_seek(self, value):
        # value is percent 0..100
        if not self.vlc_available or self.vlc_player is None:
            return
        try:
            if self.vlc_player.get_length() <= 0:
                return
            frac = float(value) / 100.0
            self.vlc_player.set_position(frac)
        except Exception:
            pass

    def _update_playback_position(self):
        if not self.vlc_available or self.vlc_player is None:
            return
        try:
            length = self.vlc_player.get_length()  # ms
            if length and length > 0:
                time_ms = self.vlc_player.get_time()
                if time_ms < 0:
                    time_ms = 0
                pos = 0.0
                try:
                    pos = (time_ms / length) * 100.0
                except Exception:
                    pos = 0.0
                self.play_pos_var.set(pos)
                self.play_time_var.set(f"{self._ms_to_mmss(time_ms)}/{self._ms_to_mmss(length)}")
            # schedule next update
            self.root.after(500, self._update_playback_position)
        except Exception:
            pass

    def _ms_to_mmss(self, ms):
        try:
            s = int(ms // 1000)
            m = s // 60
            s = s % 60
            return f"{m:02d}:{s:02d}"
        except Exception:
            return "00:00"

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
            try:
                self.start_feedback("Searching duplicates")
            except Exception:
                pass
            self.status_var.set(f"Scanning directory for duplicates: {directory}")
            self.progress_var.set(0)
            
            # Switch to duplicates mode columns
            self.current_mode = 'duplicates'
            self._setup_duplicates_columns()
            
            # Clear the table
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Print initial message to the status
            self.status_var.set("Scanning for duplicates. This may take a while...")
            
            # Find duplicates with progress callback
            def update_progress(value):
                self.progress_var.set(value)
                self.root.update_idletasks()
            
            # Disable delete button until results are ready
            try:
                self.delete_selected_button.config(state=tk.DISABLED)
            except Exception:
                pass

            duplicates = find_duplicate_songs(directory, tolerance_sec, self.progress_var.set)
            
            # Clear the table for fresh results
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Display only duplicate results
            if duplicates:
                # Darker color palette (avoid blues that clash with selected row)
                colors = [
                    "#FFB3B3",  # soft rose
                    "#FFCC99",  # warm apricot
                    "#B3E6B3",  # muted green
                    "#D6C9A9",  # warm khaki
                    "#FFAD80",  # deeper peach
                    "#FFB6D9",  # dusty pink
                    "#C8EDE0",  # soft teal
                    "#FFD98E",  # golden
                    "#FFE6CC",  # light caramel
                    "#FFCCA6",  # muted coral
                    "#EBA6C5",  # rose
                    "#C9A6E6",  # lavender (not blue)
                    "#FFEA66",  # warm yellow
                    "#80C9B3",  # darker mint
                    "#EFA6C5",  # pale rose
                ]

                for i, group in enumerate(duplicates):
                    # Use a tag to color each group differently
                    tag_name = f"group{i}"
                    color = colors[i % len(colors)]
                    # Use slightly darker text color when background is light
                    self.tree.tag_configure(tag_name, background=color)
                    
                    for j, file_path in enumerate(group):
                        filename = os.path.basename(file_path)

                        # Extract metadata for duplicate display
                        meta = self._get_file_metadata(file_path)

                        self.tree.insert(
                            "", 
                            tk.END, 
                            values=(
                                file_path,
                                meta.get('title') or filename,
                                meta.get('artists') or "",
                                meta.get('album') or "",
                                meta.get('bitrate') or "",
                                meta.get('length') or "",
                                meta.get('size_mb') or "",
                                meta.get('bpm') or "",
                                meta.get('year') or "",
                                meta.get('has_cover', 0)
                            ),
                            tags=(tag_name,)
                        )
                
                self.status_var.set(f"Found {len(duplicates)} groups of duplicate files.")
                try:
                    self.stop_feedback(f"Found {len(duplicates)} groups")
                except Exception:
                    pass
                # Enable delete button now that results are shown
                try:
                    self.delete_selected_button.config(state=tk.NORMAL)
                except Exception:
                    pass
            else:
                self.status_var.set("No duplicate files found.")
                try:
                    self.stop_feedback("No duplicates")
                except Exception:
                    pass
                messagebox.showinfo("Results", "No duplicate files found.")
                try:
                    self.delete_selected_button.config(state=tk.DISABLED)
                except Exception:
                    pass
            
            # Update progress bar to complete
            self.progress_var.set(100)
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during duplicate search: {str(e)}")

    def delete_selected_files(self):
        """Delete files selected in the treeview (with confirmation)."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No files selected for deletion.")
            return

        # Gather file paths and normalize them
        file_paths = [os.path.normpath(self.tree.set(item, "filepath")) for item in selected]
        # Limit preview text length for confirmation
        preview = "\n".join(file_paths[:10])
        more = len(file_paths) - 10
        if more > 0:
            preview += f"\n... and {more} more"

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the following {len(file_paths)} file(s)?\n\n{preview}"
        )

        if not confirm:
            return


        # Try to use send2trash to move to Recycle Bin. If not available, offer to install it.
        use_send2trash = False
        send2trash_func = None
        try:
            from send2trash import send2trash
            use_send2trash = True
            send2trash_func = send2trash
        except Exception:
            # Offer to install send2trash
            install = messagebox.askyesno(
                "send2trash not installed",
                "The 'send2trash' package is not installed.\n\n"
                "To move files to the Recycle Bin (safer), install it now?\n\n"
                "Yes: Attempt to install via pip.\nNo: Files will be permanently deleted."
            )
            if install:
                try:
                    import subprocess, sys
                    self.status_var.set("Installing send2trash...")
                    self.root.update_idletasks()
                    subprocess.run([sys.executable, "-m", "pip", "install", "send2trash"], check=False)
                    try:
                        from send2trash import send2trash
                        use_send2trash = True
                        send2trash_func = send2trash
                    except Exception:
                        use_send2trash = False
                        send2trash_func = None
                except Exception:
                    use_send2trash = False
                    send2trash_func = None
            else:
                proceed = messagebox.askyesno(
                    "Permanent Delete",
                    "You chose not to install 'send2trash'.\nDo you want to proceed with permanent deletion?"
                )
                if not proceed:
                    return

        deleted = []
        failed = []

        for item, path in zip(selected, file_paths):
            try:
                # Normalize and verify path exists
                path = os.path.normpath(path)
                if os.path.exists(path) and os.path.isfile(path):
                    try:
                        if use_send2trash and send2trash_func:
                            send2trash_func(path)
                        else:
                            os.remove(path)
                        deleted.append(path)
                        try:
                            self.tree.delete(item)
                        except Exception:
                            pass
                    except Exception as e:
                        failed.append((path, str(e)))
                else:
                    failed.append((path, "File not found or is not a file"))
                    try:
                        self.tree.delete(item)
                    except Exception:
                        pass
            except Exception as e:
                failed.append((path, str(e)))

        # Update UI and report results
        if deleted:
            messagebox.showinfo("Deleted", f"Successfully deleted {len(deleted)} file(s).")
            self.status_var.set(f"Deleted {len(deleted)} file(s).")
        if failed:
            msgs = "\n".join([f"{p}: {m}" for p, m in failed[:10]])
            if len(failed) > 10:
                msgs += f"\n... and {len(failed)-10} more"
            messagebox.showerror("Delete Errors", f"Failed to delete {len(failed)} file(s):\n\n{msgs}")
            self.status_var.set(f"Delete completed with {len(failed)} failures.")

        # If no more items, disable delete button
        if not self.tree.get_children():
            try:
                self.delete_selected_button.config(state=tk.DISABLED)
            except Exception:
                pass

    def rename_files(self):
        """Placeholder for rename files feature"""
        messagebox.showinfo(
            "Rename Files",
            "This feature will rename files to remove illegal characters.\n\n"
            "Coming soon: Remove illegal characters from filenames/titles."
        )

    def quality_check(self):
        """Analyze audio quality using spectrum analysis"""
        # Create dialog to choose scan mode
        dialog = tk.Toplevel(self.root)
        dialog.title("Quality Check - Select Scan Mode")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_reqwidth() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_reqheight() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text="Select scan mode:", font=('Arial', 12, 'bold')).pack(pady=20)
        
        scan_mode = tk.StringVar(value="")
        
        def on_folder_scan():
            scan_mode.set("folder")
            dialog.destroy()
        
        def on_file_scan():
            scan_mode.set("files")
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="📁 Scan Folder", command=on_folder_scan, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🎵 Scan Selected Files", command=on_file_scan, width=20).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(dialog, text="Folder: Scan all audio files in a folder\nSelected Files: Choose specific audio files", 
                 justify=tk.CENTER).pack(pady=10)
        
        dialog.wait_window()
        
        if not scan_mode.get():
            return
        
        # Get files based on scan mode
        files_to_scan = []
        if scan_mode.get() == "folder":
            directory = filedialog.askdirectory(title="Select folder to analyze audio quality")
            if not directory:
                return
            # Collect all audio files from directory
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wav', '.aac', '.ogg', '.wma')):
                        files_to_scan.append(os.path.join(root, file))
        else:
            files = filedialog.askopenfilenames(
                title="Select audio files to analyze",
                filetypes=[
                    ("Audio Files", "*.mp3 *.flac *.m4a *.wav *.aac *.ogg *.wma"),
                    ("All Files", "*.*")
                ]
            )
            if not files:
                return
            files_to_scan = list(files)
        
        if not files_to_scan:
            messagebox.showinfo("No Files", "No audio files found.")
            return
        
        # Start quality check in a separate thread
        threading.Thread(target=self._quality_check_thread, args=(files_to_scan,), daemon=True).start()
    
    def _quality_check_thread(self, files_to_scan):
        """Thread function to analyze audio quality without blocking the GUI"""
        try:
            try:
                self.start_feedback("Analyzing audio quality")
            except Exception:
                pass
            self.status_var.set(f"Analyzing audio quality for {len(files_to_scan)} files...")
            self.progress_var.set(0)
            
            # Switch to quality check mode columns
            self.current_mode = 'quality_check'
            self._setup_quality_check_columns()
            
            # Clear the table
            self.root.after(0, self.tree.delete, *self.tree.get_children())
            
            # Analyze each file
            results = []
            for i, filepath in enumerate(files_to_scan):
                # Get basic metadata first (outside try-except)
                metadata = self._get_file_metadata(filepath)
                file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
                metadata_bitrate = self._get_metadata_bitrate(filepath)
                
                try:
                    # Perform spectrum analysis
                    self.status_var.set(f"Analyzing spectrum: {os.path.basename(filepath)} ({i+1}/{len(files_to_scan)})")
                    real_bitrate, cutoff_freq = self._analyze_spectrum(filepath)
                    
                    # Convert cutoff frequency to kHz
                    cutoff_freq_khz = f"{cutoff_freq / 1000:.1f}" if cutoff_freq else 'N/A'
                    
                    # Determine if there's a mismatch (Fake detection)
                    is_dismatch = self._check_bitrate_mismatch(metadata_bitrate, real_bitrate)
                    
                    results.append({
                        'filepath': filepath,
                        'filename': os.path.basename(filepath),
                        'title': metadata.get('title', ''),
                        'bitrate_metadata': metadata_bitrate,
                        'real_bitrate': real_bitrate if real_bitrate else 'Unknown',
                        'file_size_mb': file_size_mb,
                        'cutoff_frequency': cutoff_freq_khz,
                        'is_dismatch': is_dismatch
                    })
                    
                    # Update progress
                    progress = int((i + 1) / len(files_to_scan) * 100)
                    self.progress_var.set(progress)
                    
                except Exception as e:
                    print(f"Error analyzing {filepath}: {e}")
                    results.append({
                        'filepath': filepath,
                        'filename': os.path.basename(filepath),
                        'title': metadata.get('title', ''),
                        'bitrate_metadata': metadata_bitrate,
                        'real_bitrate': 'Error',
                        'file_size_mb': file_size_mb,
                        'cutoff_frequency': 'Error',
                        'is_dismatch': ''
                    })
                    continue
            
            # Display results
            self.root.after(0, self._display_quality_check_results, results)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Quality Check Error", f"Error during quality check:\n\n{str(e)}")
        finally:
            try:
                self.stop_feedback()
            except Exception:
                pass
            self.progress_var.set(0)
            self.status_var.set(f"Quality check complete: {len(results)} files analyzed")
    
    def _get_metadata_bitrate(self, file_path):
        """Extract bitrate from file metadata"""
        try:
            from mutagen import File as MutagenFile
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                return "N/A"
            
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'bitrate'):
                bitrate = audio_file.info.bitrate
                if bitrate > 10000:
                    bitrate = bitrate // 1000
                return f"{bitrate} kbps"
            
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                if hasattr(info, 'bitrate'):
                    bitrate = info.bitrate
                    if bitrate > 10000:
                        bitrate = bitrate // 1000
                    return f"{bitrate} kbps"
                elif file_path.lower().endswith('.flac'):
                    return "Lossless (FLAC)"
                elif file_path.lower().endswith('.wav'):
                    return "Lossless (WAV)"
            
            return "N/A"
        except Exception as e:
            print(f"Error getting bitrate for {file_path}: {e}")
            return "N/A"
    
    def _check_bitrate_mismatch(self, metadata_bitrate, real_bitrate):
        """Check if there's a mismatch between metadata and real bitrate.
        Returns 'Fake' if mismatch detected, empty string otherwise."""
        if not metadata_bitrate or not real_bitrate or metadata_bitrate == 'N/A' or real_bitrate == 'Unknown':
            return ''
        
        # Extract numeric values from bitrate strings
        try:
            # Handle formats like "320 kbps", "~320 kbps", "Lossless (FLAC)", etc.
            import re
            
            # If either is lossless, no mismatch
            if 'Lossless' in metadata_bitrate or 'Lossless' in real_bitrate:
                return ''
            
            # Extract numbers from metadata bitrate
            metadata_match = re.search(r'(\d+)', metadata_bitrate)
            if not metadata_match:
                return ''
            metadata_kbps = int(metadata_match.group(1))
            
            # Extract numbers from real bitrate
            real_match = re.search(r'(\d+)', real_bitrate)
            if not real_match:
                return ''
            real_kbps = int(real_match.group(1))
            
            # Allow tolerance: if difference is more than 64 kbps, it's suspicious
            # Example: 320 kbps file detected as 128 kbps or lower = Fake
            if abs(metadata_kbps - real_kbps) > 64:
                return 'Fake'
            
            return ''
            
        except Exception as e:
            print(f"Error checking bitrate mismatch: {e}")
            return ''
    
    def _analyze_spectrum(self, file_path):
        """Analyze audio spectrum to detect frequency cutoff.
        Uses intelligent window sampling to avoid silent sections and breakdowns."""
        try:
            import librosa
            import numpy as np
            from mutagen import File as MutagenFile
            
            # Get total duration without loading entire file
            audio_file = MutagenFile(file_path)
            total_duration = audio_file.info.length
            
            if total_duration < 10:
                # Short file - load entirely
                y, sr = librosa.load(file_path, sr=None)
                if len(y) < sr * 2:
                    return None, None
                
                n_fft = 4096
                D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=n_fft)), ref=np.max)
                freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
                avg_spectrum = np.mean(D, axis=1)
                cutoff_freq = self._detect_frequency_cutoff(freqs, avg_spectrum)
                estimated_bitrate = self._estimate_bitrate_from_cutoff(cutoff_freq)
                
                filesize_bitrate, mb_per_min = self._estimate_bitrate_from_file_size(file_path)
                if cutoff_freq is None or mb_per_min >= 2.2 or (mb_per_min >= 1.7 and cutoff_freq < 18000) or (mb_per_min >= 1.3 and cutoff_freq < 16000):
                    estimated_bitrate = filesize_bitrate
                    if cutoff_freq is None and 'Lossless' in filesize_bitrate:
                        cutoff_freq = int(22050)  # Assume standard sample rate
                
                return estimated_bitrate, cutoff_freq
            
            # Configuration for longer files
            snippet_duration = 8  # seconds per snippet for initial scan
            num_candidates = 15  # number of positions to sample
            top_k = 4  # analyze only top K windows in detail
            
            # Calculate sampling positions evenly distributed across track
            candidate_positions = []
            for i in range(num_candidates):
                # Distribute evenly, avoiding first/last 5 seconds
                position = 5 + (i * (total_duration - 10) / (num_candidates - 1)) if num_candidates > 1 else total_duration / 2
                if position + snippet_duration <= total_duration:
                    candidate_positions.append(position)
            
            # First pass: Quick scan with low resolution to find high-energy windows
            n_fft_quick = 2048  # Lower resolution for speed
            candidate_scores = []
            
            for offset in candidate_positions:
                # Load small snippet
                y_snippet, sr = librosa.load(file_path, sr=None, offset=offset, duration=snippet_duration)
                
                # Quick STFT
                D = np.abs(librosa.stft(y_snippet, n_fft=n_fft_quick))
                D_db = librosa.amplitude_to_db(D, ref=np.max)
                
                # Calculate high-frequency energy (16-22 kHz)
                freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft_quick)
                hf_mask = (freqs >= 16000) & (freqs <= 22000)
                
                if np.any(hf_mask):
                    hf_energy = D_db[hf_mask, :]
                    hf_score = np.percentile(hf_energy, 90) if hf_energy.size > 0 else -120
                else:
                    hf_score = -120
                
                candidate_scores.append({
                    'offset': offset,
                    'score': hf_score
                })
            
            # Select top K positions
            candidate_scores.sort(key=lambda x: x['score'], reverse=True)
            top_positions = [c['offset'] for c in candidate_scores[:top_k]]
            
            # Second pass: Detailed analysis on selected windows
            n_fft = 4096  # Higher resolution
            cutoffs = []
            
            for offset in top_positions:
                # Load snippet with higher quality
                y_segment, sr = librosa.load(file_path, sr=None, offset=offset, duration=snippet_duration)
                
                # High-resolution spectrum analysis
                D = librosa.amplitude_to_db(np.abs(librosa.stft(y_segment, n_fft=n_fft)), ref=np.max)
                freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
                avg_spectrum = np.mean(D, axis=1)
                
                # Detect cutoff
                cutoff = self._detect_frequency_cutoff(freqs, avg_spectrum)
                if cutoff:
                    cutoffs.append(cutoff)
            
            # Use lowest cutoff found (most conservative estimate)
            if cutoffs:
                cutoff_freq = min(cutoffs)
            else:
                cutoff_freq = None
            
            # Estimate bitrate from cutoff
            estimated_bitrate = self._estimate_bitrate_from_cutoff(cutoff_freq)
            
            # ALWAYS run file size estimation as verification
            filesize_bitrate, mb_per_min = self._estimate_bitrate_from_file_size(file_path)
            
            # Decision logic: Compare spectrum analysis with file size
            if cutoff_freq is None:
                # No cutoff detected - trust file size
                estimated_bitrate = filesize_bitrate
                if 'Lossless' in filesize_bitrate:
                    cutoff_freq = int(sr / 2)  # Nyquist frequency
            elif mb_per_min >= 2.2:
                # File size indicates 320 kbps - trust file size over spectrum
                estimated_bitrate = filesize_bitrate
            elif mb_per_min >= 1.7 and cutoff_freq < 18000:
                # File size indicates 256 kbps but spectrum suggests lower - trust file size
                estimated_bitrate = filesize_bitrate
            elif mb_per_min >= 1.3 and cutoff_freq < 16000:
                # File size indicates 192 kbps but spectrum suggests lower - trust file size
                estimated_bitrate = filesize_bitrate
            elif 'Lossless' in filesize_bitrate:
                # Lossless detected by file size
                estimated_bitrate = filesize_bitrate
                cutoff_freq = int(sr / 2)
            # Otherwise, trust the spectrum analysis cutoff detection
            
            return estimated_bitrate, cutoff_freq
            
        except ImportError:
            messagebox.showerror("Missing Library", "librosa library is required for spectrum analysis.\n\nInstall with: pip install librosa")
            return None, None
        except Exception as e:
            print(f"Spectrum analysis failed: {str(e)}")
            return None, None
    
    def _detect_frequency_cutoff(self, freqs, spectrum):
        """Detect frequency cutoff from spectrum - improved detection"""
        try:
            import numpy as np
            
            # Focus on high frequency range where MP3 cutoffs occur
            high_freq_start = 10000  # Start from 10kHz
            high_freq_mask = freqs >= high_freq_start
            high_freqs = freqs[high_freq_mask]
            high_spectrum = spectrum[high_freq_mask]
            
            if len(high_spectrum) < 10:
                return None
            
            # Method 1: Look for sharp drops (brick wall)
            spectrum_diff = np.diff(high_spectrum)
            drop_threshold = -3  # dB drop per frequency bin
            
            for i in range(len(spectrum_diff) - 5):
                if all(spectrum_diff[i:i+5] < drop_threshold):
                    return int(high_freqs[i])
            
            # Method 2: Energy threshold method with rolling average
            window_size = 5
            if len(high_spectrum) >= window_size:
                smoothed = np.convolve(high_spectrum, np.ones(window_size)/window_size, mode='valid')
                smoothed_freqs = high_freqs[:len(smoothed)]
                
                noise_floor = np.percentile(smoothed, 5)
                energy_threshold = noise_floor + 6
                
                above_threshold = smoothed > energy_threshold
                if np.any(above_threshold):
                    last_energy_idx = np.where(above_threshold)[0][-1]
                    
                    if last_energy_idx < len(smoothed_freqs) - 10:
                        remaining_energy = smoothed[last_energy_idx+5:]
                        if len(remaining_energy) > 0 and np.mean(remaining_energy) < energy_threshold:
                            return int(smoothed_freqs[last_energy_idx])
            
            # Method 3: Frequency band energy comparison
            band_size = 500  # Hz
            band_energies = []
            band_centers = []
            
            for freq_start in range(10000, 22000, band_size):
                band_mask = (freqs >= freq_start) & (freqs < freq_start + band_size)
                if np.any(band_mask):
                    band_energy = np.mean(spectrum[band_mask])
                    band_energies.append(band_energy)
                    band_centers.append(freq_start + band_size/2)
            
            if len(band_energies) > 2:
                band_energies = np.array(band_energies)
                for i in range(len(band_energies) - 1):
                    if band_energies[i] - band_energies[i+1] > 10:  # 10dB drop
                        return int(band_centers[i])
            
            # Method 4: Statistical analysis
            if len(high_spectrum) > 20:
                mean_energy = np.mean(high_spectrum[:len(high_spectrum)//2])
                std_energy = np.std(high_spectrum[:len(high_spectrum)//2])
                low_energy_threshold = mean_energy - 2 * std_energy
                
                for i in range(len(high_spectrum) - 10):
                    if all(high_spectrum[i:i+10] < low_energy_threshold):
                        return int(high_freqs[i])
            
            return None
            
        except Exception as e:
            print(f"Cutoff detection failed: {str(e)}")
            return None
    
    def _estimate_bitrate_from_cutoff(self, cutoff_freq):
        """Estimate bitrate based on frequency cutoff"""
        if cutoff_freq is None:
            return "Unknown"
        
        if cutoff_freq >= 20000:
            return "320 kbps or Lossless"
        elif cutoff_freq >= 19000:
            return "~320 kbps"
        elif cutoff_freq >= 18000:
            return "~256 kbps"
        elif cutoff_freq >= 17000:
            return "~224 kbps"
        elif cutoff_freq >= 16000:
            return "~192 kbps"
        elif cutoff_freq >= 15000:
            return "~160 kbps"
        elif cutoff_freq >= 14000:
            return "~128 kbps"
        elif cutoff_freq >= 12000:
            return "~128 kbps (CBR)"
        elif cutoff_freq >= 11000:
            return "~112 kbps"
        elif cutoff_freq >= 10000:
            return "~96 kbps"
        else:
            return "~64 kbps or lower"
    
    def _estimate_bitrate_from_file_size(self, file_path):
        """Estimate bitrate based on file size and duration - SECONDARY CHECK"""
        try:
            from mutagen import File as MutagenFile
            from pathlib import Path
            
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            audio_file = MutagenFile(file_path)
            
            if audio_file and hasattr(audio_file, 'info'):
                duration = getattr(audio_file.info, 'length', 0)
                if duration > 0:
                    duration_minutes = duration / 60
                    ext = Path(file_path).suffix.lower()
                    
                    # Check for lossless formats first
                    if ext == '.flac':
                        return "Lossless (FLAC)", file_size_mb / duration_minutes
                    elif ext == '.wav':
                        return "Lossless (WAV)", file_size_mb / duration_minutes
                    elif ext == '.aiff':
                        return "Lossless (AIFF)", file_size_mb / duration_minutes
                    
                    # For lossy formats - estimate based on MB per minute
                    mb_per_minute = file_size_mb / duration_minutes if duration_minutes > 0 else 0
                    
                    # File size based estimation
                    if mb_per_minute >= 2.2:
                        return "~320 kbps", mb_per_minute
                    elif mb_per_minute >= 1.7:
                        return "~256 kbps", mb_per_minute
                    elif mb_per_minute >= 1.3:
                        return "~192 kbps", mb_per_minute
                    elif mb_per_minute >= 1.0:
                        return "~160 kbps", mb_per_minute
                    elif mb_per_minute >= 0.8:
                        return "~128 kbps", mb_per_minute
                    elif mb_per_minute >= 0.6:
                        return "~96 kbps", mb_per_minute
                    else:
                        return f"~{int(mb_per_minute * 128)} kbps", mb_per_minute
            
            return "Unknown", 0
            
        except Exception as e:
            print(f"File size estimation failed: {str(e)}")
            return "Unknown", 0
    
    def _setup_quality_check_columns(self):
        """Configure treeview columns for quality check mode"""
        self.tree['columns'] = ()
        for col in self.tree.get_children():
            self.tree.delete(col)
        
        columns = ('filepath', 'title', 'bitrate_metadata', 'real_bitrate', 'file_size_mb', 'cutoff_frequency', 'is_dismatch')
        self.tree['columns'] = columns
        
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=0, stretch=False)
        
        self.tree.heading('filepath', text='File Name', command=lambda: self._sort_by_column('filepath'))
        self.tree.column('filepath', width=500, anchor=tk.W)
        
        self.tree.heading('title', text='Title', command=lambda: self._sort_by_column('title'))
        self.tree.column('title', width=400, anchor=tk.W)
        
        self.tree.heading('bitrate_metadata', text='Bit Rate (Original)', command=lambda: self._sort_by_column('bitrate_metadata'))
        self.tree.column('bitrate_metadata', width=100, anchor=tk.CENTER)
        
        self.tree.heading('real_bitrate', text='Real Bitrate', command=lambda: self._sort_by_column('real_bitrate'))
        self.tree.column('real_bitrate', width=100, anchor=tk.CENTER)
        
        self.tree.heading('file_size_mb', text='File Size (MB)', command=lambda: self._sort_by_column('file_size_mb'))
        self.tree.column('file_size_mb', width=100, anchor=tk.CENTER)
        
        self.tree.heading('cutoff_frequency', text='Frequency (kHz)', command=lambda: self._sort_by_column('cutoff_frequency'))
        self.tree.column('cutoff_frequency', width=100, anchor=tk.CENTER)
        
        self.tree.heading('is_dismatch', text='IsDismatch', command=lambda: self._sort_by_column('is_dismatch'))
        self.tree.column('is_dismatch', width=100, anchor=tk.CENTER)
    
    def _sort_by_column(self, col):
        """Sort treeview contents by the specified column"""
        # Get all items
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Try to sort numerically if possible, otherwise alphabetically
        try:
            # Try numeric sort first
            items.sort(key=lambda x: float(x[0].replace('~', '').replace(' kbps', '').replace(' MB', '').replace(' kHz', '').replace('Lossless', '99999').replace('Unknown', '-1').replace('N/A', '-1').replace('Error', '-1').replace('Fake', '1').replace(',', '') or -1), reverse=getattr(self, f'_sort_{col}_reverse', False))
        except (ValueError, AttributeError):
            # Fall back to string sort
            items.sort(key=lambda x: x[0].lower(), reverse=getattr(self, f'_sort_{col}_reverse', False))
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        # Toggle sort direction for next time
        setattr(self, f'_sort_{col}_reverse', not getattr(self, f'_sort_{col}_reverse', False))
    
    def _display_quality_check_results(self, results):
        """Display quality check results in the treeview"""
        self.tree.delete(*self.tree.get_children())
        
        for result in results:
            values = (
                result['filepath'],
                result['title'],
                result['bitrate_metadata'],
                result['real_bitrate'],
                f"{result['file_size_mb']:.2f}",
                result['cutoff_frequency'],
                result['is_dismatch']
            )
            
            item_id = self.tree.insert('', tk.END, values=values)
        
        messagebox.showinfo(
            "Quality Check Complete",
            f"Analysis complete:\n\n"
            f"Total files analyzed: {len(results)}"
        )

    def analyze_collection(self):
        """Load and display Traktor collection."""
        # First, try to load saved collection path
        collection_path = load_collection_path()
        
        if collection_path and os.path.exists(collection_path):
            # Ask if user wants to use saved path or browse for new one
            use_saved = messagebox.askyesno(
                "Collection Path",
                f"Use previously saved collection path?\n\n{collection_path}"
            )
            if not use_saved:
                collection_path = filedialog.askdirectory(title="Select Traktor Collection folder")
        else:
            # Prompt user to select collection folder
            collection_path = filedialog.askdirectory(title="Select Traktor Collection folder")
        
        if not collection_path:
            return
        
        # Save the collection path
        save_collection_path(collection_path)
        
        # Start collection parsing in a separate thread
        threading.Thread(target=self._analyze_collection_thread, args=(collection_path,), daemon=True).start()
    
    def _analyze_collection_thread(self, collection_path):
        """Thread function to parse collection without blocking the GUI"""
        try:
            try:
                self.start_feedback("Analyzing collection")
            except Exception:
                pass
            self.status_var.set(f"Loading Traktor collection from: {collection_path}")
            self.progress_var.set(0)
            
            # Switch to collection mode columns
            self.current_mode = 'collection'
            self._setup_collection_columns()
            
            # Clear the table
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            self.status_var.set("Parsing collection.nml...")
            
            # Parse collection
            tracks = parse_traktor_collection(collection_path)
            
            if not tracks:
                self.status_var.set("No tracks found in collection or error parsing collection.nml")
                try:
                    self.stop_feedback("No tracks")
                except Exception:
                    pass
                messagebox.showwarning("No Tracks", "Could not parse collection or no tracks found.")
                return
            
            # Display tracks in treeview
            for i, track in enumerate(tracks):
                filepath = track.get('filepath', '')
                # Store track metadata for later use (cover popup, etc.)
                try:
                    self.collection_tracks[filepath] = track
                except Exception:
                    pass

                cover_indicator = '🖼️' if track.get('cover_path') else ''

                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        filepath,
                        track.get('title', ''),
                        track.get('artist', ''),
                        track.get('remixer', ''),
                        track.get('producer', ''),
                        track.get('album', ''),
                        track.get('genre', ''),
                        track.get('label', ''),
                        track.get('catalogno', ''),
                        track.get('release_date', ''),
                        track.get('track_number', ''),
                        track.get('bpm', ''),
                        track.get('key', ''),
                        track.get('key_text', ''),
                        track.get('bitrate', ''),
                        track.get('length', ''),
                        track.get('autogain', ''),
                        track.get('rating', ''),
                        track.get('mix', ''),
                        track.get('comment', ''),
                        track.get('lyrics', ''),
                        cover_indicator
                    )
                )
                # Update progress
                self.progress_var.set((i / len(tracks)) * 100)
                self.root.update_idletasks()
            
            self.status_var.set(f"Loaded {len(tracks)} tracks from Traktor collection.")
            self.progress_var.set(100)
            try:
                self.stop_feedback(f"Loaded {len(tracks)} tracks")
            except Exception:
                pass
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error loading collection: {str(e)}")
    
    def _on_collection_column_click(self, event):
        """Handle column header clicks for sorting in collection mode."""
        if self.current_mode != 'collection':
            return
        

    # (load_more feature removed)
        
        # Get the column that was clicked
        

    def _open_in_explorer(self, path):
        """Open the given file path in the system file explorer and select it in the table."""
        try:
            # Strip whitespace
            path = str(path).strip() if path else ""
            
            if not path:
                messagebox.showerror("Error", "Path is empty or invalid")
                return
            
            # Handle file:// URLs
            if path.startswith("file://"):
                try:
                    from urllib.parse import unquote
                    parsed = path[7:]  # remove 'file://'
                    # Handle Windows paths that may have leading /
                    if parsed.startswith('/') and len(parsed) > 2 and parsed[2] == ':':
                        parsed = parsed[1:]
                    path = unquote(parsed)
                except Exception as e:
                    print(f"Error parsing file:// URL: {e}")
                    return
            
            # Decode URL encoding
            if '%' in path:
                try:
                    from urllib.parse import unquote
                    path = unquote(path)
                except Exception:
                    pass
            
            # Normalize path
            path = os.path.normpath(path)
            
            # Debug: print what we're trying to open
            print(f"DEBUG _open_in_explorer: normalized path = '{path}'")
            print(f"DEBUG: exists = {os.path.exists(path)}, isdir = {os.path.isdir(path) if os.path.exists(path) else 'N/A'}")
            
            # Find and select the row in the treeview with matching filepath
            for item in self.tree.get_children():
                item_filepath = self.tree.set(item, "filepath").strip()
                if os.path.normpath(item_filepath) == path:
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    break
            
            # If it's a directory, just open it
            if os.path.isdir(path):
                try:
                    os.startfile(path)
                    return
                except Exception as e:
                    print(f"Error opening directory: {e}")
                    pass
            
            # If it's a file, open folder and select file
            if os.path.exists(path) and os.path.isfile(path):
                folder = os.path.dirname(path)
                filename = os.path.basename(path)
                print(f"DEBUG: opening folder='{folder}', selecting file='{filename}'")
                try:
                    # Use explorer /select to highlight the file
                    subprocess.Popen(f'explorer /select,"{path}"', shell=True)
                    return
                except Exception as e:
                    print(f"Error with /select approach: {e}")
                    try:
                        # Fallback: just open the folder
                        subprocess.Popen(f'explorer "{folder}"', shell=True)
                        return
                    except Exception as e2:
                        print(f"Error opening folder fallback: {e2}")
            
            # Path doesn't exist
            print(f"DEBUG: path does not exist: {path}")
            messagebox.showerror("File Not Found", f"File or folder not found:\n{path}")
        except Exception as e:
            print(f"DEBUG _open_in_explorer exception: {e}")
            messagebox.showerror("Error", f"Could not open file explorer: {e}")

    def _on_tree_right_click(self, event):
        """Handle right-click on treeview row. Show context menu."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Select the row
        self.tree.selection_set(item)
        
        # Get filepath from row
        filepath = self.tree.set(item, "filepath")
        if not filepath:
            return
        
        # Create context menu
        context_menu = tk.Menu(self.tree, tearoff=False)
        context_menu.add_command(
            label="Open in Explorer",
            command=lambda: self._open_in_explorer(filepath)
        )
        
        # Show context menu at cursor position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def _show_cover_popup(self, cover_path):
        """Show cover art in a popup window. Uses PIL if available."""
        try:
            from PIL import Image, ImageTk
            pil_available = True
        except Exception:
            pil_available = False

        if not cover_path or not os.path.exists(cover_path):
            messagebox.showinfo("Cover Art", "Cover image not found.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Cover Art")

        try:
            if pil_available:
                img = Image.open(cover_path)
                img.thumbnail((600, 600))
                photo = ImageTk.PhotoImage(img)
            else:
                # Fallback to Tk PhotoImage (supports PNG/GIF)
                photo = tk.PhotoImage(file=cover_path)

            label = tk.Label(popup, image=photo)
            label.image = photo  # keep ref
            label.pack()
        except Exception as e:
            popup.destroy()
            messagebox.showerror("Image Error", f"Could not open cover image: {e}")




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