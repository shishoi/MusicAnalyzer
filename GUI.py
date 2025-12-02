import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

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
        
        # Add buttons
        self.analyze_button = ttk.Button(
            self.button_frame, 
            text="🔍 Analyze Files", 
            command=self.analyze_files,
            width=20
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(
            self.button_frame, 
            text="💾 Save Changes", 
            command=self.save_changes,
            width=20,
            state=tk.DISABLED  # Initially disabled
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Add tooltip to Save Changes button
        save_tooltip_text = "Saves analysis results:\n- MP3 tags: Title, BPM, Key\n- Traktor CUE points: Intro, Build, Drop, Outro"
        ToolTip(self.save_button, save_tooltip_text)
        
        self.find_duplicates_button = ttk.Button(
            self.button_frame, 
            text="🗐 Find Duplicate Files", 
            command=self.find_duplicates,
            width=20
        )
        self.find_duplicates_button.pack(side=tk.LEFT, padx=5)

        self.collection_button = ttk.Button(
            self.button_frame,
            text="🎵 Analyze Collection",
            command=self.analyze_collection,
            width=20
        )
        self.collection_button.pack(side=tk.LEFT, padx=5)

        # Button to delete selected files (enabled when duplicate results shown)
        self.delete_selected_button = ttk.Button(
            self.button_frame,
            text="🗑️ Delete Selected",
            command=self.delete_selected_files,
            width=20,
            state=tk.DISABLED
        )
        self.delete_selected_button.pack(side=tk.LEFT, padx=5)

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
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

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
        self.duplicates_columns = ("filepath", "title", "artists", "bitrate", "length", "size_mb", "BPM", "year")
        
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
        self.tree.heading("bitrate", text="Bit Rate")
        self.tree.heading("length", text="Length")
        self.tree.heading("size_mb", text="Size (MB)")
        self.tree.heading("BPM", text="BPM")
        self.tree.heading("year", text="Year")
        
        # Define columns width
        self.tree.column("filepath", width=450)
        self.tree.column("title", width=250)
        self.tree.column("artists", width=180)
        self.tree.column("bitrate", width=30)
        self.tree.column("length", width=30)
        self.tree.column("size_mb", width=30)
        self.tree.column("BPM", width=30)
        self.tree.column("year", width=30)
    
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
        self.tree.column("title", width=180)
        self.tree.column("artist", width=120)
        self.tree.column("remixer", width=100)
        self.tree.column("producer", width=100)
        self.tree.column("album", width=120)
        self.tree.column("genre", width=80)
        self.tree.column("label", width=100)
        self.tree.column("catalogno", width=80)
        self.tree.column("release_date", width=80)
        self.tree.column("track_number", width=60)
        self.tree.column("bpm", width=50)
        self.tree.column("key", width=40)
        self.tree.column("key_text", width=60)
        self.tree.column("bitrate", width=80)
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


    def _get_file_metadata(self, file_path):
        """Return metadata for a file: title, bitrate (e.g. '320 kbps'), length (mm:ss), size_mb (string), artists, bpm, year."""
        meta = {
            'title': None,
            'bitrate': None,
            'length': None,
            'size_mb': None,
            'artists': None,
            'bpm': None,
            'year': None
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
                                meta.get('bitrate') or "",
                                meta.get('length') or "",
                                meta.get('size_mb') or "",
                                meta.get('bpm') or "",
                                meta.get('year') or ""
                            ),
                            tags=(tag_name,)
                        )
                
                self.status_var.set(f"Found {len(duplicates)} groups of duplicate files.")
                # Enable delete button now that results are shown
                try:
                    self.delete_selected_button.config(state=tk.NORMAL)
                except Exception:
                    pass
            else:
                self.status_var.set("No duplicate files found.")
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
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error loading collection: {str(e)}")
    
    def _on_collection_column_click(self, event):
        """Handle column header clicks for sorting in collection mode."""
        if self.current_mode != 'collection':
            return
        
        # Get the column that was clicked
        region = self.tree.identify_region(event.x, event.y)
        if region != "heading":
            return
        
        col = self.tree.identify_column(event.x)
        col_index = int(col[1:]) - 1
        
        if col_index < 0 or col_index >= len(self.collection_columns):
            return
        
        column = self.collection_columns[col_index]
        
        # Determine sort direction
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Get all items
        items = self.tree.get_children()
        values_list = []
        
        for item in items:
            values = self.tree.item(item, 'values')
            values_list.append((item, values))
        
        # Sort based on the column
        try:
            # Try to sort numerically first
            values_list.sort(
                key=lambda x: float(x[1][col_index]) if x[1][col_index] else 0,
                reverse=self.sort_reverse
            )
        except (ValueError, IndexError):
            # Fall back to string sorting
            values_list.sort(
                key=lambda x: str(x[1][col_index]) if col_index < len(x[1]) else "",
                reverse=self.sort_reverse
            )
        
        # Reorder items in treeview
        for idx, (item, _) in enumerate(values_list):
            self.tree.move(item, '', idx)

    def _open_in_explorer(self, path):
        """Open the given file path in the system file explorer."""
        try:
            if os.path.isdir(path):
                os.startfile(path)
            else:
                # Open containing folder and select file
                if os.path.exists(path):
                    # Windows-specific: use explorer /select,
                    subprocess_cmd = f'explorer /select,"{path}"'
                    try:
                        os.system(subprocess_cmd)
                    except Exception:
                        os.startfile(os.path.dirname(path))
                else:
                    messagebox.showerror("File Not Found", f"Path not found: {path}")
        except Exception as e:
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