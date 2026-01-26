import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment
from datetime import datetime
import shutil
import xml.etree.ElementTree as ET
import json

""" 
Audio and music analysis - BPM, Key, CUE points
Detect and write new cues points into Traktor files (NML) 
"""

class AudioAnalyzer:
    def __init__(self, file_path):
        """
        Initialize the audio analyzer with a file path
        
        Args:
            file_path (str): Path to the audio file (MP3, WAV, etc.)
        """
        self.file_path = file_path
        self.y = None
        self.sr = None
        self.tempo = None
        self.key = None
        self.camelot_key = None
        self.traktor_key = None
        self.traktor_key_text = None
        self.cue_points = {}
        
        # Load the file
        self._load_audio()
    
    def _load_audio(self):
        """Load the audio file using librosa"""
        try:
            self.y, self.sr = librosa.load(self.file_path, sr=None)
            print(f"File loaded successfully. Sample rate: {self.sr}Hz")
        except Exception as e:
            print(f"Error loading file: {e}")
    
    def analyze_bpm(self):
        """Detect the BPM (tempo) of the song"""
        if self.y is None:
            print("No audio file loaded.")
            return None
        
        try:
            # Use librosa's tempo detection algorithm
            onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
            self.tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=self.sr)[0]
            print(f"BPM: {self.tempo:.1f}")
            return self.tempo
        except Exception as e:
            print(f"Error detecting BPM: {e}")
            return None
    
    def analyze_key(self):
        """Detect the musical key of the song"""
        if self.y is None:
            print("No audio file loaded.")
            return None
        
        try:
            # Calculate chromagram
            chroma = librosa.feature.chroma_cqt(y=self.y, sr=self.sr)
            
            # Average the chromagram over time
            chroma_means = np.mean(chroma, axis=1)
            
            # List of possible keys
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_index = np.argmax(chroma_means)
            
            # Check if major or minor
            if self._is_major(chroma):
                self.key = f"{keys[key_index]} Major"
            else:
                minor_idx = (key_index + 9) % 12  # Relative minor
                self.key = f"{keys[minor_idx]} Minor"
            
            # Get Traktor notation
            self.traktor_key, self.traktor_key_text = self._get_traktor_notation(self.key)
            self.camelot_key = self._get_camelot_notation(self.key)
            
            # Print both notations
            print(f"KEY: {self.camelot_key}")
            print(f"TRAKTOR KEY: {self.traktor_key} ({self.traktor_key_text})")
            
            return self.key
        except Exception as e:
            print(f"Error detecting key: {e}")
            return None
    
    def detect_cue_points(self, sensitivity=1.0):
        """
        Detect four main CUE points in a track:
        1. Intro - beginning of the track
        2. Build-up - musical development
        3. Chorus/Drop - main section
        4. Outro - end/transition section
        
        Args:
            sensitivity (float): Sensitivity for change detection (1.0 is normal)
        
        Returns:
            dict: Dictionary with 4 main CUE points (time in seconds)
        """
        if self.y is None:
            print("No audio file loaded.")
            return {}
        
        try:
            # Get song length
            song_length = len(self.y) / self.sr
            
            # 1. Analyze energy and rhythm
            onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=self.sr)
            beat_times = librosa.frames_to_time(beats, sr=self.sr)
            
            # 2. Calculate RMS energy throughout the song
            hop_length = 512
            rms = librosa.feature.rms(y=self.y, hop_length=hop_length)[0]
            times = librosa.times_like(rms, sr=self.sr, hop_length=hop_length)
            
            # 3. Detect significant changes in energy
            # Divide song into segments
            num_segments = 100
            segment_length = len(rms) // num_segments
            segment_energies = []
            
            for i in range(num_segments):
                start = i * segment_length
                end = start + segment_length
                if end <= len(rms):
                    segment_energies.append(np.mean(rms[start:end]))
            
            # 4. Identify significant changes
            # Create a list of significant changes
            changes = []
            for i in range(1, len(segment_energies)):
                change = segment_energies[i] - segment_energies[i-1]
                changes.append((i, change))
            
            # Sort changes by magnitude (largest to smallest)
            significant_changes = sorted(changes, key=lambda x: abs(x[1]), reverse=True)
            
            # 5. Identify CUE points based on changes
            # Intro: beginning of the song, typically just after the very start
            intro_time = min(10.0, song_length * 0.05)  # or 5% into the song, whichever is earlier
            
            # Find the drop/chorus - significant positive change in energy
            positive_changes = [c for c in significant_changes if c[1] > 0]
            # Typically the drop is between 25% and 50% of the song
            likely_drops = [c for c in positive_changes if 0.2 <= (c[0]/num_segments) <= 0.6]
            
            if likely_drops:
                drop_segment = likely_drops[0][0]  # Most significant positive change
                drop_time = drop_segment * song_length / num_segments
            else:
                drop_time = song_length * 0.35  # Default: 35% into the song
            
            # Build-up: before the drop
            # Typically 15-30 seconds before the drop
            build_time = max(intro_time + 10, drop_time - 20)
            
            # Outro: towards end of song
            outro_time = song_length * 0.85  # 85% into the song
            
            # Make sure points are reasonable and not overlapping
            min_distance = 10  # Minimum distance between CUE points (in seconds)
            
            # Adjust points that are too close
            if build_time - intro_time < min_distance:
                build_time = intro_time + min_distance
            
            if drop_time - build_time < min_distance:
                drop_time = build_time + min_distance
            
            if outro_time - drop_time < min_distance:
                outro_time = drop_time + min_distance
            
            # Store CUE points
            self.cue_points = {
                'intro': intro_time,
                'build': build_time,
                'drop': drop_time,
                'outro': outro_time
            }
            
            print(f"Found 4 CUE points:")
            print(f"Intro: {self._format_time(intro_time)}")
            print(f"Build: {self._format_time(build_time)}")
            print(f"Drop: {self._format_time(drop_time)}")
            print(f"Outro: {self._format_time(outro_time)}")
            
            return self.cue_points
            
        except Exception as e:
            print(f"Error detecting CUE points: {e}")
            return {}
    
    def _format_time(self, seconds):
        """Format time in seconds nicely"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _get_traktor_notation(self, key_name):
        """
        Convert standard musical key to Traktor KEY format
        Map standard key to both Traktor's KEY (e.g., "6m") and KEY TEXT (e.g., "A Minor")
        
        Args:
            key_name (str): Key name in standard notation (e.g., "C Major")
            
        Returns:
            tuple: (traktor_key, traktor_key_text) 
                  e.g., ("8B", "C Major") or ("8d", "C Major") in Traktor's format
        """
        # Parse the key string
        parts = key_name.split(' ')
        note = parts[0]
        mode = parts[1]
        
        # Traktor's KEY format mapping
        # For Traktor: d = major (dur), m = minor (moll)
        key_map = {
        'C Major':  ('8B',  'C'),
        'C# Major': ('3B',  'C#'),
        'Db Major': ('3B',  'Db'),
        'D Major':  ('10B', 'D'),
        'D# Major': ('5B',  'D#'),
        'Eb Major': ('5B',  'Eb'),
        'E Major':  ('12B', 'E'),
        'F Major':  ('7B',  'F'),
        'F# Major': ('2B',  'F#'),
        'Gb Major': ('2B',  'Gb'),
        'G Major':  ('9B',  'G'),
        'G# Major': ('4B',  'G#'),
        'Ab Major': ('4B',  'Ab'),
        'A Major':  ('11B', 'A'),
        'A# Major': ('6B',  'A#'),
        'Bb Major': ('6B',  'Bb'),
        'B Major':  ('1B',  'B'),

        'C Minor':  ('5A',  'Cm'),
        'C# Minor': ('12A', 'C#m'),
        'Db Minor': ('12A', 'Dbm'),
        'D Minor':  ('7A',  'Dm'),
        'D# Minor': ('2A',  'D#m'),
        'Eb Minor': ('2A',  'Ebm'),
        'E Minor':  ('9A',  'Em'),
        'F Minor':  ('4A',  'Fm'),
        'F# Minor': ('11A', 'F#m'),
        'Gb Minor': ('11A', 'Gbm'),
        'G Minor':  ('6A',  'Gm'),
        'G# Minor': ('1A',  'G#m'),
        'Ab Minor': ('1A',  'Abm'),
        'A Minor':  ('8A',  'Am'),
        'A# Minor': ('3A',  'A#m'),
        'Bb Minor': ('3A',  'Bbm'),
        'B Minor':  ('10A', 'Bm'),
        }

        
        # Get Traktor's KEY and KEY TEXT formats
        full_key = f"{note} {mode}"
        if full_key in key_map:
            return key_map[full_key]
        else:
            # If not found, return original format
            short_mode = "m" if mode == "Minor" else "d"
            return (f"?{short_mode}", f"{note}{'' if mode == 'Major' else 'm'}")
    
    def _get_camelot_notation(self, key_name):
        """
        Convert standard musical key to Camelot Wheel notation
        
        Args:
            key_name (str): Key name in standard notation (e.g., "C Major")
            
        Returns:
            str: Key in Camelot notation (e.g., "8B - C Major")
        """
        # Camelot wheel mapping: [major_position, minor_position]
        camelot_map = {
            'C': ['8B', '5A'],
            'C#': ['3B', '12A'],
            'Db': ['3B', '12A'],
            'D': ['10B', '7A'],
            'D#': ['5B', '2A'],
            'Eb': ['5B', '2A'],
            'E': ['12B', '9A'],
            'F': ['7B', '4A'],
            'F#': ['2B', '11A'],
            'Gb': ['2B', '11A'],
            'G': ['9B', '6A'],
            'G#': ['4B', '1A'],
            'Ab': ['4B', '1A'],
            'A': ['11B', '8A'],
            'A#': ['6B', '3A'],
            'Bb': ['6B', '3A'],
            'B': ['1B', '10A']
        }
        
        # Parse the key string
        parts = key_name.split(' ')
        note = parts[0]
        mode = parts[1]
        
        # Get the Camelot notation
        if note in camelot_map:
            index = 0 if mode == 'Major' else 1
            camelot_notation = camelot_map[note][index]
            return f"{camelot_notation} - {key_name}"
        else:
            return key_name
    
    def _is_major(self, chroma):
        """Check if the song is in a major or minor key"""
        # Calculate major and minor profiles
        major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
        minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])
        
        # Calculate average chromagram
        chroma_means = np.mean(chroma, axis=1)
        
        # Calculate correlation for all possible keys
        major_correlation = np.zeros(12)
        minor_correlation = np.zeros(12)
        
        for i in range(12):
            # Shift profile for all key possibilities
            major_correlation[i] = np.corrcoef(np.roll(major_profile, i), chroma_means)[0, 1]
            minor_correlation[i] = np.corrcoef(np.roll(minor_profile, i), chroma_means)[0, 1]
        
        # Choose the highest correlation
        max_major_corr = np.max(major_correlation)
        max_minor_corr = np.max(minor_correlation)
        
        # If major correlation is higher, the song is in major
        return max_major_corr > max_minor_corr

    def plot_waveform_with_cues(self):
        """Display waveform with marked CUE points"""
        if self.y is None:
            print("No audio file loaded.")
            return
        
        plt.figure(figsize=(15, 5))
        
        # Display waveform
        plt.plot(np.linspace(0, len(self.y)/self.sr, len(self.y)), self.y, alpha=0.5)
        
        # Mark CUE points if they exist
        if self.cue_points:
            colors = {'intro': 'g', 'build': 'y', 'drop': 'r', 'outro': 'b'}
            for cue_type, time in self.cue_points.items():
                plt.axvline(x=time, color=colors.get(cue_type, 'r'), linestyle='--', alpha=0.7, 
                           label=f"{cue_type.capitalize()}: {self._format_time(time)}")
        
        plt.title('Waveform with CUE Points')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.legend()
        plt.tight_layout()
        plt.show()


class TraktorNMLEditor:
    def __init__(self, nml_path):
        """
        Module for safely editing Traktor NML files
        
        Args:
            nml_path (str): Path to collection.nml file
        """
        self.nml_path = nml_path
        self.backup_dir = os.path.join(os.path.dirname(nml_path), "backups")
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def backup_collection(self):
        """Create a backup of the current Collection file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"collection_backup_{timestamp}.nml")
        
        shutil.copy2(self.nml_path, backup_path)
        print(f"Created backup at: {backup_path}")
        
        return backup_path
    
    def add_cue_points(self, audio_path, cue_points, cue_names=None):
        """
        Add CUE points to a specific track
        
        Args:
            audio_path (str): Path to the audio file
            cue_points (dict): Dictionary with CUE types and times in seconds
            cue_names (dict, optional): Custom names for CUE points
        
        Returns:
            bool: Whether the operation was successful
        """
        # Back up before any changes
        self.backup_collection()
        
        try:
            # Read the file
            tree = ET.parse(self.nml_path)
            root = tree.getroot()
            
            # Find the specific file
            audio_filename = os.path.basename(audio_path)
            entry_found = False
            
            for entry in root.findall(".//ENTRY"):
                location = entry.find("LOCATION")
                if location is not None:
                    file = location.get("FILE")
                    if file and file.lower() == audio_filename.lower():
                        entry_found = True
                        
                        # Convert times to Traktor format (milliseconds)
                        traktor_cues = {
                            'intro': int(cue_points['intro'] * 1000),
                            'build': int(cue_points['build'] * 1000),
                            'drop': int(cue_points['drop'] * 1000),
                            'outro': int(cue_points['outro'] * 1000)
                        }
                        
                        # Default names if custom names not provided
                        if cue_names is None:
                            cue_names = {
                                'intro': "Intro",
                                'build': "Build",
                                'drop': "Drop",
                                'outro': "Outro"
                            }
                        
                        # Remove existing CUE points with the same names
                        for cue in list(entry.findall("CUE_V2")):
                            name = cue.get("NAME")
                            if name in cue_names.values():
                                entry.remove(cue)
                        
                        # Add new CUE points
                        for i, (cue_type, start_time) in enumerate(traktor_cues.items()):
                            cue = ET.SubElement(entry, "CUE_V2")
                            cue.set("NAME", cue_names[cue_type])
                            cue.set("DISPL_ORDER", str(i))
                            cue.set("TYPE", "0")  # 0 = Hot Cue
                            cue.set("START", str(start_time))
                            cue.set("LEN", "0")  # Single point, not a section
                            cue.set("REPEATS", "-1")
                            cue.set("HOTCUE", str(i+1))  # Hot Cue number (1-8)
                
            if not entry_found:
                print(f"File {audio_filename} not found in Traktor collection")
                return False
            
            # Save temporary file
            temp_path = self.nml_path + ".temp"
            tree.write(temp_path, encoding="UTF-8", xml_declaration=True)
            
            # Validate
            try:
                check_tree = ET.parse(temp_path)
                valid_xml = True
            except:
                valid_xml = False
            
            if valid_xml:
                # Replace original file
                os.replace(temp_path, self.nml_path)
                print(f"Successfully updated: {audio_filename}")
                return True
            else:
                os.remove(temp_path)
                print("XML validation failed")
                return False
            
        except Exception as e:
            print(f"Error updating NML file: {str(e)}")
            return False


# Functions for finding duplicate songs 
def find_duplicate_songs(directory, tolerance_sec=3.0, progress_callback=None):
    """
    Find duplicate songs using a faster multi-factor approach
    
    Args:
        directory (str): Path to music directory
        tolerance_sec (float): Tolerance in seconds for length differences (default: 3 seconds)
        progress_callback (function): Optional callback function to report progress (0-100)
    
    Returns:
        list: List of groups of duplicate files
    """
    import mutagen
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import hashlib
    import os.path
    
    print(f"Scanning directory: {directory}")
    print("Looking for audio files...")
    
    # Collect all audio files
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg')):
                full_path = os.path.join(root, file)
                audio_files.append(full_path)
    
    print(f"Found {len(audio_files)} audio files")
    if len(audio_files) == 0:
        return []
    
    # Function to extract file metadata
    def extract_metadata(file_path):
        try:
            # Get metadata with mutagen
            audio = mutagen.File(file_path, easy=True)
            
            # Create metadata dictionary
            metadata = {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'duration': None,
                'title': None,
                'artist': None,
                'album': None,
                'contrib_artist': None,
                'bitrate': None
            }
            
            # Extract duration
            if audio is not None and hasattr(audio, "info") and hasattr(audio.info, "length"):
                metadata['duration'] = audio.info.length
            
            # Extract other metadata if available
            if audio is not None:
                if 'title' in audio:
                    metadata['title'] = audio['title'][0] if audio['title'] else None
                if 'artist' in audio:
                    metadata['artist'] = audio['artist'][0] if audio['artist'] else None
                # Try to extract album and contributing/album artist
                if 'album' in audio:
                    metadata['album'] = audio['album'][0] if audio['album'] else None
                # Common alternate keys for contributing/album artist
                contrib = None
                if 'albumartist' in audio:
                    contrib = audio['albumartist'][0] if audio['albumartist'] else None
                elif 'contributingartist' in audio:
                    contrib = audio['contributingartist'][0] if audio['contributingartist'] else None
                elif 'performer' in audio:
                    contrib = audio['performer'][0] if audio['performer'] else None
                if contrib:
                    metadata['contrib_artist'] = contrib
                if hasattr(audio.info, "bitrate"):
                    metadata['bitrate'] = audio.info.bitrate
            
            return metadata
        except Exception as e:
            print(f"\nError processing file {file_path}: {e}")
            return {'path': file_path, 'error': str(e)}
    
    # Process files in parallel
    file_metadata = []
    total_files = len(audio_files)
    
    if progress_callback:
        progress_callback(5)
    
    # Process in parallel with ThreadPoolExecutor
    processed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_file = {executor.submit(extract_metadata, file): file for file in audio_files}
        
        for future in as_completed(future_to_file):
            metadata = future.result()
            if 'error' not in metadata and metadata['duration'] is not None:
                file_metadata.append(metadata)
            
            processed += 1
            if progress_callback:
                progress = 5 + (45 * (processed / total_files))
                progress_callback(progress)
    
    print("\nMetadata extraction complete")
    print("Looking for duplicates...")
    
    # Sort by duration for initial grouping
    file_metadata.sort(key=lambda x: x['duration'])
    
    # Group files by similar duration
    duration_groups = []
    current_group = []
    
    for i, metadata in enumerate(file_metadata):
        if i == 0:
            current_group = [metadata]
        else:
            if abs(metadata['duration'] - current_group[0]['duration']) <= tolerance_sec:
                current_group.append(metadata)
            else:
                if len(current_group) > 1:
                    duration_groups.append(current_group)
                current_group = [metadata]
    
    # Add the last group if it has potential duplicates
    if len(current_group) > 1:
        duration_groups.append(current_group)
    
    # Update progress
    if progress_callback:
        progress_callback(50)
    
    # For each duration group, further analyze for duplicates
    duplicates = []
    total_groups = len(duration_groups)
    
    # Version keywords that indicate different track versions
    VERSION_KEYWORDS = [
        'remix', 'rmx', 'radio edit', 'radio version', 'original mix',
        'extended', 'extended mix', 'club mix', 'dub', 'instrumental',
        'acapella', 'a cappella', 'vocal mix', 'club version', 'edit',
        'remaster', 'remastered', 'vip', 'bootleg', 'mashup', 'rework',
        'radio', 'club', 'version', 'original', 'mix'
    ]

    def normalize_string(text):
        """Normalize string for comparison: lowercase, remove separators, special chars."""
        if not text:
            return ""
        import re
        # Convert to lowercase
        text = text.lower()
        # Remove file extensions
        text = re.sub(r'\.(mp3|wav|flac|m4a|aac|ogg|wma|aiff|alac)$', '', text)
        # Replace common separators with spaces
        text = re.sub(r'[_\-\.+]', ' ', text)
        # Remove special characters (keep only alphanumeric and spaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def extract_version_keywords(text):
        """Extract version keywords from text."""
        if not text:
            return set()
        text_lower = text.lower()
        found = set()
        for keyword in VERSION_KEYWORDS:
            # Use word boundaries to avoid partial matches
            import re
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                found.add(keyword)
        return found

    def strip_version_keywords(text):
        """Remove version keywords from text for comparison."""
        if not text:
            return text
        result = text
        for keyword in VERSION_KEYWORDS:
            # Case-insensitive replacement with word boundaries
            import re
            result = re.sub(r'\b' + re.escape(keyword) + r'\b', '', result, flags=re.IGNORECASE)
        # Clean up extra spaces
        result = ' '.join(result.split())
        return result

    # Function to calculate filename similarity
    def filename_similarity(name1, name2):
        """Calculate similarity between two filenames using RapidFuzz with normalization."""
        # Normalize both names
        name1_norm = normalize_string(name1)
        name2_norm = normalize_string(name2)
        
        # Strip version keywords
        name1_stripped = strip_version_keywords(name1_norm)
        name2_stripped = strip_version_keywords(name2_norm)
        
        # Use RapidFuzz for similarity (falls back to basic comparison if unavailable)
        try:
            from rapidfuzz import fuzz
            # token_set_ratio ignores word order and duplicates - best for song names
            similarity = fuzz.token_set_ratio(name1_stripped, name2_stripped) / 100.0
            return similarity
        except ImportError:
            # Fallback to Levenshtein if RapidFuzz not available
            try:
                import Levenshtein
                distance = Levenshtein.distance(name1_stripped, name2_stripped)
                max_len = max(len(name1_stripped), len(name2_stripped))
                if max_len == 0:
                    return 1.0
                return 1.0 - (distance / max_len)
            except ImportError:
                # Simple fallback if neither library is available
                if not name1_stripped or not name2_stripped:
                    return 0.0
                common_chars = sum(1 for c in name1_stripped if c in name2_stripped)
                max_len = max(len(name1_stripped), len(name2_stripped))
                if max_len == 0:
                    return 0.0
                return common_chars / max_len
    
    # Find true duplicates in each duration group
    for i, group in enumerate(duration_groups):
        # If very small group, use duration only
        if len(group) == 2:
            duplicates.append([item['path'] for item in group])
            continue
            
        # For larger groups, use additional factors
        processed_in_group = set()
        
        for j, item1 in enumerate(group):
            if item1['path'] in processed_in_group:
                continue
                
            # Start a new duplicate group
            duplicate_group = [item1['path']]
            processed_in_group.add(item1['path'])
            
            for k in range(j+1, len(group)):
                item2 = group[k]
                
                if item2['path'] in processed_in_group:
                    continue
                
                # Calculate similarity factors
                factors = []
                
                # Similar size factor
                size_ratio = min(item1['size'], item2['size']) / max(item1['size'], item2['size'])
                factors.append(size_ratio)
                
                # Similar bitrate factor
                if item1['bitrate'] and item2['bitrate']:
                    bitrate_ratio = min(item1['bitrate'], item2['bitrate']) / max(item1['bitrate'], item2['bitrate'])
                    factors.append(bitrate_ratio)
                
                # Filename similarity
                name_sim = filename_similarity(item1['filename'], item2['filename'])
                factors.append(name_sim)
                
                # Artist/title match
                if item1['artist'] and item2['artist'] and item1['artist'] == item2['artist']:
                    factors.append(1.0)  # Strong factor for same artist
                
                if item1['title'] and item2['title'] and item1['title'] == item2['title']:
                    factors.append(1.0)  # Strong factor for same title
                
                # Calculate overall similarity
                if factors:
                    similarity = sum(factors) / len(factors)
                    
                    # Threshold for considering duplicates
                    threshold = 0.8
                    
                    if similarity >= threshold:
                        duplicate_group.append(item2['path'])
                        processed_in_group.add(item2['path'])
            
            # If found duplicates
            if len(duplicate_group) > 1:
                duplicates.append(duplicate_group)
        
        # Update progress
        if progress_callback:
            progress = 50 + (49 * ((i + 1) / total_groups))
            progress_callback(min(progress, 99))
    
    # Final progress update
    if progress_callback:
        progress_callback(100)

    # Prioritize groups that have high filename/title similarity and consistent size/length
    try:
        # Build metadata map for quick lookup
        metadata_map = {m['path']: m for m in file_metadata}

        def score_group(group):
            # group: list of file paths
            n = len(group)
            if n <= 1:
                return 0.0

            # Pairwise filename similarity average
            sim_sum = 0.0
            pairs = 0
            for i in range(n):
                for j in range(i+1, n):
                    name1 = os.path.basename(group[i])
                    name2 = os.path.basename(group[j])
                    sim_sum += filename_similarity(name1, name2)
                    pairs += 1
            fname_sim = (sim_sum / pairs) if pairs else 0.0

            # Size consistency (average min/max ratio)
            sizes = []
            durations = []
            titles = []
            albums = []
            contribs = []
            for p in group:
                m = metadata_map.get(p)
                if m:
                    sizes.append(m.get('size') or 0)
                    if m.get('duration'):
                        durations.append(m.get('duration'))
                    if m.get('title'):
                        titles.append(m.get('title'))
                    if m.get('album'):
                        albums.append(m.get('album'))
                    if m.get('contrib_artist'):
                        contribs.append(m.get('contrib_artist'))

            size_sim = 0.0
            if len(sizes) >= 2:
                ratios = []
                for i in range(len(sizes)):
                    for j in range(i+1, len(sizes)):
                        a, b = sizes[i], sizes[j]
                        if max(a, b) > 0:
                            ratios.append(min(a, b) / max(a, b))
                if ratios:
                    size_sim = sum(ratios) / len(ratios)

            # Duration consistency: small range -> high score
            dur_sim = 0.0
            if durations:
                dur_range = max(durations) - min(durations)
                # if within tolerance_sec -> high, else reduce (clamp)
                dur_sim = max(0.0, 1.0 - (dur_range / max(tolerance_sec, 1e-6)))
                if dur_sim > 1.0:
                    dur_sim = 1.0

            # Title match factor: proportion of matching titles
            title_factor = 0.0
            if titles:
                # Normalize and strip version keywords from titles
                from collections import Counter
                normalized_titles = []
                for t in titles:
                    if t:
                        t_norm = normalize_string(t)
                        t_stripped = strip_version_keywords(t_norm)
                        normalized_titles.append(t_stripped)
                
                c = Counter(normalized_titles)
                if c:
                    most_common_count = c.most_common(1)[0][1]
                    title_factor = most_common_count / len(titles)

            # Album match factor
            album_factor = 0.0
            if albums:
                from collections import Counter as _CounterA
                ca = _CounterA([a.lower() for a in albums if a])
                if ca:
                    album_factor = ca.most_common(1)[0][1] / len(albums)

            # Contributing artist match factor
            contrib_factor = 0.0
            if contribs:
                from collections import Counter as _CounterC
                cc = _CounterC([c.lower() for c in contribs if c])
                if cc:
                    contrib_factor = cc.most_common(1)[0][1] / len(contribs)

            # Weighted score: filename (0.30), size (0.07), duration (0.07), title (0.13), album (0.13), contrib artist (0.30)
            
            # Minimum metadata threshold: require strong artist OR title match
            # This prevents grouping completely different songs with similar duration
            metadata_match = max(contrib_factor, title_factor)
            if metadata_match < 0.5:
                # If neither artist nor title match well, reject this group
                return 0.0
            
            # Detect version keyword mismatches
            version_penalty = 1.0
            for p in group:
                fname_versions = extract_version_keywords(os.path.basename(p))
                m = metadata_map.get(p)
                title_versions = extract_version_keywords(m.get('title', '')) if m else set()
                all_versions = fname_versions | title_versions
                
                # Compare with first file in group
                if p != group[0]:
                    fname_v0 = extract_version_keywords(os.path.basename(group[0]))
                    m0 = metadata_map.get(group[0])
                    title_v0 = extract_version_keywords(m0.get('title', '')) if m0 else set()
                    all_v0 = fname_v0 | title_v0
                    
                    # If version keywords differ, apply penalty
                    if all_versions != all_v0 and (all_versions or all_v0):
                        version_penalty = 0.5
                        break
            
            score = (
                0.30 * fname_sim
                + 0.07 * size_sim
                + 0.07 * dur_sim
                + 0.13 * title_factor
                + 0.13 * album_factor
                + 0.30 * contrib_factor
            ) * version_penalty
            return score

        # Compute scores and sort groups descending
        scored = [(score_group(g), g) for g in duplicates]
        scored.sort(key=lambda x: x[0], reverse=True)
        duplicates = [g for s, g in scored]
    except Exception:
        # If anything goes wrong, fall back to original order
        pass

    print(f"Found {len(duplicates)} groups of duplicate files")
    
    return duplicates

def print_duplicate_groups(duplicates):
    """Print duplicate groups in a readable format"""
    if not duplicates:
        print("No duplicates found")
        return
    
    print("\nDuplicate search results:")
    print("=" * 80)
    
    for i, group in enumerate(duplicates):
        print(f"\nGroup {i+1}:")
        for j, file_path in enumerate(group):
            try:
                # Get length and additional information
                y, sr = librosa.load(file_path, sr=None, duration=10)
                duration = librosa.get_duration(filename=file_path)
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                
                # Print file information
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # in MB
                print(f"  {j+1}. {os.path.basename(file_path)}")
                print(f"     Path: {file_path}")
                print(f"     Length: {minutes:02d}:{seconds:02d}")
                print(f"     Size: {file_size:.2f} MB")
            except Exception as e:
                print(f"  {j+1}. {file_path} (Error: {e})")
        print("-" * 40)

def analyze_audio_file(file_path):
    """
    Convenient function to analyze an audio file and create CUE
    
    Args:
        file_path (str): Path to the audio file
    """
    analyzer = AudioAnalyzer(file_path)
    
    print("Analyzing file:", file_path)
    print("-" * 50)
    
    # Analyze BPM and KEY
    bpm = analyzer.analyze_bpm()
    key = analyzer.analyze_key()
    
    # Detect CU


# Collection management

CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".collection_config.json")

def save_collection_path(path):
    """Save collection folder path to config file."""
    try:
        config = {"collection_path": path}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"Error saving collection path: {e}")
        return False

def load_collection_path():
    """Load collection folder path from config file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("collection_path")
    except Exception as e:
        print(f"Error loading collection path: {e}")
    return None

def format_bitrate(bitrate_value):
    """Convert bitrate from raw value to kbps format."""
    try:
        br = int(bitrate_value)
        if br > 1000:
            return f"{br // 1000} kbps"
        return f"{br} kbps"
    except (ValueError, TypeError):
        return bitrate_value

def format_bpm(bpm_value):
    """Format BPM as integer (zero decimal places)."""
    try:
        return str(int(float(bpm_value)))
    except (ValueError, TypeError):
        return bpm_value if bpm_value else ""

def format_duration(duration_sec):
    """Convert duration from seconds to MM:SS format."""
    try:
        sec = int(duration_sec)
        minutes = sec // 60
        seconds = sec % 60
        return f"{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return duration_sec if duration_sec else ""

def parse_traktor_collection(collection_path):
    """
    Parse Traktor collection.nml file and extract comprehensive track metadata.
    
    Args:
        collection_path (str): Path to the collection folder
    
    Returns:
        list: List of dicts with track metadata including all Traktor tags
    """
    import urllib.parse
    
    nml_path = os.path.join(collection_path, "collection.nml")
    
    if not os.path.exists(nml_path):
        print(f"collection.nml not found at: {nml_path}")
        return []
    
    tracks = []
    try:
        tree = ET.parse(nml_path)
        root = tree.getroot()
        
        # Debug: print root tag
        print(f"Root tag: {root.tag}")
        
        # Extract all ENTRY elements (tracks)
        entries = root.findall(".//ENTRY")
        print(f"Found {len(entries)} entries in collection.nml")
        
        for idx, entry in enumerate(entries):
            track = {}

            # Extract basic attributes from ENTRY element
            # Traktor can store location as:
            # 1. LOCATION subelement with VOLUME, DIR, FILE attributes
            # 2. LOCATION attribute (direct file:// URL or path)
            # 3. DIR + FILE attributes directly
            
            location = ''
            
            # Try LOCATION subelement first (most common in recent Traktor)
            loc_elem = entry.find('LOCATION')
            if loc_elem is not None:
                volume = loc_elem.get('VOLUME', '')
                dir_attr = loc_elem.get('DIR', '')
                file_attr = loc_elem.get('FILE', '')
                
                # Reconstruct path: VOLUME + DIR + FILE
                # VOLUME contains drive letter (e.g., "C:")
                # DIR contains path with colons as separators (e.g., "/:Users/:home/:Music/")
                # FILE contains filename (e.g., "song.mp3")
                
                parts = []
                if volume:
                    # Volume is already "C:" format
                    vol = volume.strip()
                    if vol:
                        parts.append(vol)
                
                if dir_attr:
                    # Remove leading/trailing slashes, replace / with \, remove colons used as separators
                    d = dir_attr.strip('/').replace('/', '\\').replace(':', '')
                    if d:
                        parts.append(d)
                
                if file_attr:
                    f = file_attr.strip()
                    if f:
                        parts.append(f)
                
                if parts:
                    location = '\\'.join(parts)
                    # Final cleanup for valid Windows path
                    location = location.replace('\\\\', '\\')
            
            # Fallback: try LOCATION attribute
            if not location:
                location = entry.get('LOCATION', '') or ''
            
            # Fallback: try DIR + FILE attributes on ENTRY
            if not location:
                dir_attr = entry.get('DIR', '') or entry.get('DIRECTORY', '')
                file_attr = entry.get('FILE', '') or entry.get('FILENAME', '')
                if dir_attr or file_attr:
                    try:
                        location = os.path.join(dir_attr, file_attr)
                    except Exception:
                        location = (dir_attr or '') + (file_attr or '')

            # If location is a file:// URL, parse it
            if location.startswith('file://'):
                try:
                    parsed = urllib.parse.urlparse(location)
                    path = urllib.parse.unquote(parsed.path)
                    # On Windows, urlparse path may start with /C:/
                    if path.startswith('/') and len(path) > 2 and path[2] == ':':
                        path = path[1:]
                    location = path
                except Exception:
                    pass

            # Decode percent-encoding if present
            if '%' in location:
                try:
                    location = urllib.parse.unquote(location)
                except Exception:
                    pass

            track['filepath'] = location

            track['title'] = entry.get('TITLE', '')
            track['artist'] = entry.get('ARTIST', '')
            track['album'] = entry.get('ALBUM', '')
            track['genre'] = entry.get('GENRE', '')
            track['comment'] = entry.get('COMMENT', '')
            track['remixer'] = entry.get('REMIXER', '')
            track['producer'] = entry.get('PRODUCER', '')
            track['label'] = entry.get('LABEL', '')
            track['catalogno'] = entry.get('CATALOGNO', '')
            track['release_date'] = entry.get('RELEASE_DATE', '')
            track['mix'] = entry.get('MIX', '')
            track['lyrics'] = entry.get('LYRICS', '')
            track['track_number'] = entry.get('TRACK', '')
            track['rating'] = entry.get('RATING', '')

            # Debug first few entries
            if idx < 3:
                print(f"Entry {idx}: title='{track['title']}', artist='{track['artist']}', filepath='{track['filepath'][:50] if track['filepath'] else ''}...'")
            
            
            # Extract INFO subelement (duration, bitrate, etc)
            info = entry.find('INFO')
            if info is not None:
                track['bitrate'] = format_bitrate(info.get('BITRATE', ''))
                track['length'] = format_duration(info.get('DURATION', ''))
                track['autogain'] = info.get('AUTOGAIN', '')
            else:
                track['bitrate'] = ''
                track['length'] = ''
                track['autogain'] = ''
            
            # Extract TEMPO subelement (BPM)
            tempo = entry.find('TEMPO')
            if tempo is not None:
                bpm_raw = tempo.get('BPM', '')
                track['bpm'] = format_bpm(bpm_raw)
            else:
                track['bpm'] = ''
            
            # Extract KEY subelement (numeric key)
            key = entry.find('KEY')
            if key is not None:
                track['key'] = key.get('VALUE', '')
                track['key_text'] = key.get('TEXT', '')
            else:
                track['key'] = ''
                track['key_text'] = ''
            
            # Extract cover art (COVER element)
            cover = entry.find('COVER')
            cover_path = ''
            if cover is not None:
                # COVER element may include base64 DATA or a PATH attribute
                data = cover.get('DATA') or cover.get('IMAGE') or None
                path_attr = cover.get('PATH') or cover.get('FILE') or None
                if data:
                    # Try to decode base64 data and write to temp file
                    try:
                        import base64, tempfile, re
                        # Data may contain the mime prefix like data:image/png;base64,xxx
                        m = re.match(r"data:(.*?);base64,(.*)", data)
                        if m:
                            b64 = m.group(2)
                            ext = 'png' if 'png' in m.group(1) else 'jpg'
                        else:
                            b64 = data
                            ext = 'jpg'
                        decoded = base64.b64decode(b64)
                        tmp = tempfile.gettempdir()
                        safe_title = re.sub(r"[^0-9a-zA-Z_-]", "_", track.get('title','')[:40]) or f"cover_{idx}"
                        out_path = os.path.join(tmp, f"{safe_title}.{ext}")
                        with open(out_path, 'wb') as imgf:
                            imgf.write(decoded)
                        cover_path = out_path
                    except Exception:
                        cover_path = ''
                elif path_attr:
                    # If path is provided, try to decode percent-encoding
                    try:
                        import urllib.parse
                        p = urllib.parse.unquote(path_attr)
                        # If path is relative, join with collection_path
                        if not os.path.isabs(p):
                            p = os.path.join(collection_path, p)
                        cover_path = p
                    except Exception:
                        cover_path = path_attr
                else:
                    cover_path = ''
            track['cover_path'] = cover_path
            
            # Extract CUEPOINT data for reference
            cuepoints = entry.findall('.//CUE_POINT')
            cue_dict = {}
            for cue in cuepoints:
                cue_name = cue.get('NAME', '').upper()
                cue_pos = cue.get('START', '')
                if cue_name and cue_pos:
                    cue_dict[cue_name] = cue_pos
            if cue_dict:
                track['cuepoints'] = cue_dict
            
            tracks.append(track)
    
    except Exception as e:
        print(f"Error parsing collection.nml: {e}")
        return []
    
    return tracks