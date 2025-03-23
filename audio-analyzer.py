import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment
from pydub.utils import make_chunks

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
        self.cue_points = []
        
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
            'C Major': ('8d', 'C'),
            'C# Major': ('3d', 'C#'),
            'Db Major': ('3d', 'Db'),
            'D Major': ('10d', 'D'),
            'D# Major': ('5d', 'D#'),
            'Eb Major': ('5d', 'Eb'),
            'E Major': ('12d', 'E'),
            'F Major': ('7d', 'F'),
            'F# Major': ('2d', 'F#'),
            'Gb Major': ('2d', 'Gb'),
            'G Major': ('9d', 'G'),
            'G# Major': ('4d', 'G#'),
            'Ab Major': ('4d', 'Ab'),
            'A Major': ('11d', 'A'),
            'A# Major': ('6d', 'A#'),
            'Bb Major': ('6d', 'Bb'),
            'B Major': ('1d', 'B'),
            'C Minor': ('5m', 'Cm'),
            'C# Minor': ('12m', 'C#m'),
            'Db Minor': ('12m', 'Dbm'),
            'D Minor': ('7m', 'Dm'),
            'D# Minor': ('2m', 'D#m'),
            'Eb Minor': ('2m', 'Ebm'),
            'E Minor': ('9m', 'Em'),
            'F Minor': ('4m', 'Fm'),
            'F# Minor': ('11m', 'F#m'),
            'Gb Minor': ('11m', 'Gbm'),
            'G Minor': ('6m', 'Gm'),
            'G# Minor': ('1m', 'G#m'),
            'Ab Minor': ('1m', 'Abm'),
            'A Minor': ('8m', 'Am'),
            'A# Minor': ('3m', 'A#m'),
            'Bb Minor': ('3m', 'Bbm'),
            'B Minor': ('10m', 'Bm')
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
    
    def detect_cue_points(self, sensitivity=1.0, min_silence_len=1000):
        """
        Detect automatic CUE points
        
        Args:
            sensitivity (float): Sensitivity for change detection (1.0 is normal)
            min_silence_len (int): Minimum silence length in milliseconds
        
        Returns:
            list: List of CUE points (time in seconds)
        """
        if self.y is None:
            print("No audio file loaded.")
            return []
        
        try:
            # Detect changes in volume - start points of beats
            onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sr)
            
            # Detect significant points in the song
            onset_times = librosa.frames_to_time(onset_frames, sr=self.sr)
            
            # Extract only the most significant points
            # (for example: if there are many points, select only those with significant change)
            if len(onset_times) > 20:  # If there are too many points
                # Calculate the strength of change at each point
                onset_strengths = onset_env[onset_frames]
                
                # Sort points by strength of change
                strong_onsets_idx = np.argsort(onset_strengths)[-20:]  # 20 strongest points
                onset_times = onset_times[strong_onsets_idx]
            
            # Detect silence (for end/start of sections)
            silent_sections = self._detect_silence(None, min_silence_len, -40)
            
            # Combine all points
            all_points = list(onset_times)
            
            # Add start/end points of silent sections
            for start, end in silent_sections:
                all_points.append(start / 1000.0)  # Convert from milliseconds to seconds
                all_points.append(end / 1000.0)
            
            # Add points at fixed times (every 30 seconds)
            song_length = len(self.y) / self.sr
            for t in range(0, int(song_length), 30):
                all_points.append(float(t))
            
            # Sort and remove duplicates
            all_points = sorted(set(all_points))
            
            # Filter points that are too close
            min_distance = 15.0  # Minimum distance in seconds (increased to 15 seconds)
            filtered_points = []
            if all_points:  # Check that the array is not empty
                filtered_points = [all_points[0]]
                for point in all_points[1:]:
                    if point - filtered_points[-1] >= min_distance:
                        filtered_points.append(point)
            
            self.cue_points = filtered_points
            print(f"Found {len(self.cue_points)} CUE points")
            
            return self.cue_points
        except Exception as e:
            print(f"Error detecting CUE points: {e}")
            return []
    
    def _detect_silence(self, audio, min_silence_len, silence_thresh):
        """Detect silent sections in the audio file"""
        silence_sections = []
        try:
            # Use a simpler approach to detect silence
            # Divide audio into short segments and detect noise level in each segment
            chunk_length_ms = 500  # Segment length in milliseconds
            chunk_size = int(self.sr * chunk_length_ms / 1000)
            
            # Number of segments
            num_chunks = len(self.y) // chunk_size
            
            # Check noise level in each segment
            silent_chunks = []
            for i in range(num_chunks):
                start = i * chunk_size
                end = start + chunk_size
                chunk = self.y[start:end]
                
                # Calculate noise level
                energy = np.mean(np.abs(chunk))
                
                # If the level is below threshold, it's a silent segment
                if energy < 0.01:  # Low threshold adjusted for sensitivity
                    silent_chunks.append(i)
            
            # Combine consecutive silent segments
            silence_start = None
            for i in range(len(silent_chunks)):
                if i == 0 or silent_chunks[i] > silent_chunks[i-1] + 1:
                    if silence_start is not None:
                        # Convert to time in milliseconds
                        start_ms = silence_start * chunk_length_ms
                        end_ms = silent_chunks[i-1] * chunk_length_ms + chunk_length_ms
                        if end_ms - start_ms >= min_silence_len:
                            silence_sections.append((start_ms, end_ms))
                    silence_start = silent_chunks[i]
                
                if i == len(silent_chunks) - 1 and silence_start is not None:
                    # Handle the last silent segment
                    start_ms = silence_start * chunk_length_ms
                    end_ms = silent_chunks[i] * chunk_length_ms + chunk_length_ms
                    if end_ms - start_ms >= min_silence_len:
                        silence_sections.append((start_ms, end_ms))
            
            return silence_sections
        except Exception as e:
            print(f"Error detecting silence: {e}")
            return []
    
    def export_cue_sheet(self, output_file=None):
        """
        Create a CUE file
        
        Args:
            output_file (str): Path to output file (if None, will use original filename)
        
        Returns:
            str: Path to the created CUE file
        """
        if not self.cue_points:
            print("No CUE points detected. Run detect_cue_points first.")
            return None
        
        if output_file is None:
            base_name = os.path.splitext(self.file_path)[0]
            output_file = f"{base_name}.cue"
        
        try:
            # Create CUE file
            file_name = os.path.basename(self.file_path)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f'TITLE "Automatic CUE Sheet"\n')
                f.write(f'FILE "{file_name}" WAVE\n')
                
                for i, time in enumerate(self.cue_points):
                    # Convert time to MM:SS:FF format (minutes:seconds:frames)
                    minutes = int(time // 60)
                    seconds = int(time % 60)
                    frames = int((time % 1) * 75)  # 75 frames per second in CUE format
                    
                    f.write(f'  TRACK {i+1:02d} AUDIO\n')
                    f.write(f'    TITLE "Track {i+1}"\n')
                    f.write(f'    INDEX 01 {minutes:02d}:{seconds:02d}:{frames:02d}\n')
            
            print(f"CUE file created successfully: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error creating CUE file: {e}")
            return None
    
    def plot_waveform_with_cues(self):
        """Display waveform with marked CUE points"""
        if self.y is None:
            print("No audio file loaded.")
            return
        
        if not self.cue_points:
            print("No CUE points detected. Run detect_cue_points first.")
            return
        
        plt.figure(figsize=(15, 5))
        
        # Display waveform
        plt.plot(np.linspace(0, len(self.y)/self.sr, len(self.y)), self.y, alpha=0.5)
        
        # Mark CUE points
        for cue in self.cue_points:
            plt.axvline(x=cue, color='r', linestyle='--', alpha=0.7)
        
        plt.title('Waveform with CUE Points')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.tight_layout()
        plt.show()


# Function to find duplicate songs by length
def find_duplicate_songs(directory, tolerance_sec=3.0):
    """
    Find duplicate songs in a directory by song length
    
    Args:
        directory (str): Path to music directory
        tolerance_sec (float): Tolerance in seconds for length differences (default: 3 seconds)
    
    Returns:
        list: List of groups of duplicate files
    """
    print(f"Scanning directory: {directory}")
    print("Looking for audio files...")
    
    # Collect all audio files in the directory (including subdirectories)
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg')):
                full_path = os.path.join(root, file)
                audio_files.append(full_path)
    
    print(f"Found {len(audio_files)} audio files")
    if len(audio_files) == 0:
        return []
    
    # Find song lengths
    file_durations = {}
    for i, file_path in enumerate(audio_files):
        try:
            print(f"\rProcessing file {i+1}/{len(audio_files)}: {os.path.basename(file_path)}", end="\r")
            
            # Use librosa to find song length
            y, sr = librosa.load(file_path, sr=None, duration=10)  # Load just the start of the file to get the sample rate
            duration = librosa.get_duration(filename=file_path)
            
            # Save length and path
            file_durations[file_path] = duration
        except Exception as e:
            print(f"\nError processing file {file_path}: {e}")
    
    print("\nSong length analysis complete")
    print("Looking for duplicates...")
    
    # Find duplicates by length
    duplicates = []
    processed = set()
    
    # Sort by length
    sorted_files = sorted(file_durations.items(), key=lambda x: x[1])
    
    for i, (file1, duration1) in enumerate(sorted_files):
        if file1 in processed:
            continue
        
        similar_files = [file1]
        
        # Look for files with similar length
        for j in range(i + 1, len(sorted_files)):
            file2, duration2 = sorted_files[j]
            
            # If the difference is greater than tolerance, we can stop searching (since the array is sorted)
            if abs(duration2 - duration1) > tolerance_sec:
                break
                
            if file2 not in processed:
                similar_files.append(file2)
        
        # If duplicates found
        if len(similar_files) > 1:
            duplicates.append(similar_files)
            for file in similar_files:
                processed.add(file)
    
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
    
    # Detect CUE points
    print("\nDetecting CUE points...")
    cue_points = analyzer.detect_cue_points(sensitivity=1.2)
    
    # Display points
    if cue_points:
        print("\nDetected CUE points (in seconds):")
        for i, point in enumerate(cue_points):
            minutes = int(point // 60)
            seconds = int(point % 60)
            print(f"  {i+1:2d}: {minutes:02d}:{seconds:02d}")
    
    # Create CUE file
    cue_file = analyzer.export_cue_sheet()
    
    print("\nSummary:")
    print(f"BPM: {bpm:.1f}" if bpm else "BPM: not detected")
    print(f"KEY: {key}" if key else "KEY: not detected")
    print(f"CUE points: {len(cue_points)}")
    print(f"CUE file: {cue_file}" if cue_file else "CUE file: not created")
    
    # Visual display
    analyzer.plot_waveform_with_cues()

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  For single file analysis: python audio_analyzer.py path/to/song.mp3")
        print("  To find duplicates: python audio_analyzer.py --find-duplicates path/to/music/directory [tolerance_sec]")
        sys.exit(1)
    
    if sys.argv[1] == "--find-duplicates":
        if len(sys.argv) < 3:
            print("Please provide a path to the music directory")
            sys.exit(1)
        
        directory = sys.argv[2]
        tolerance_sec = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
        
        duplicates = find_duplicate_songs(directory, tolerance_sec)
        print_duplicate_groups(duplicates)
    else:
        file_path = sys.argv[1]
        analyze_audio_file(file_path)
