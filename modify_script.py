import re

# Read the file
with open('C:/Users/home/Documents/DJ/DEV/MusicAnalyzer/audio_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add year and BPM to metadata dictionary
old_metadata_dict = '''            metadata = {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'duration': None,
                'title': None,
                'artist': None,
                'album': None,
                'contrib_artist': None,
                'bitrate': None
            }'''

new_metadata_dict = '''            metadata = {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'duration': None,
                'title': None,
                'artist': None,
                'album': None,
                'contrib_artist': None,
                'bitrate': None,
                'year': None,
                'bpm': None
            }'''

content = content.replace(old_metadata_dict, new_metadata_dict)

# 2. Add year and BPM extraction after bitrate extraction
old_bitrate_section = '''                if hasattr(audio.info, "bitrate"):
                    metadata['bitrate'] = audio.info.bitrate

            return metadata'''

new_bitrate_section = '''                if hasattr(audio.info, "bitrate"):
                    metadata['bitrate'] = audio.info.bitrate
                
                # Extract year/date
                if 'date' in audio:
                    metadata['year'] = audio['date'][0] if audio['date'] else None
                
                # Extract BPM
                if 'bpm' in audio:
                    try:
                        metadata['bpm'] = float(audio['bpm'][0]) if audio['bpm'] else None
                    except (ValueError, TypeError):
                        pass

            return metadata'''

content = content.replace(old_bitrate_section, new_bitrate_section)

# 3. Add download site words to VERSION_KEYWORDS
old_version_keywords = '''    VERSION_KEYWORDS = [
        'remix', 'rmx', 'radio edit', 'radio version', 'original mix',
        'extended', 'extended mix', 'club mix', 'dub', 'instrumental',
        'acapella', 'a cappella', 'vocal mix', 'club version', 'edit',
        'remaster', 'remastered', 'vip', 'bootleg', 'mashup', 'rework',
        'radio', 'club', 'version', 'original', 'mix'
    ]'''

new_version_keywords = '''    VERSION_KEYWORDS = [
        'remix', 'rmx', 'radio edit', 'radio version', 'original mix',
        'extended', 'extended mix', 'club mix', 'dub', 'instrumental',
        'acapella', 'a cappella', 'vocal mix', 'club version', 'edit',
        'remaster', 'remastered', 'vip', 'bootleg', 'mashup', 'rework',
        'radio', 'club', 'version', 'original', 'mix',
        # Download site indicators
        'youtube', 'spotidownloader', 'spotidown', 'app', 'com', 'mp3',
        'v3', 'yt1z', 'net', 'download', 'free', 'converted'
    ]'''

content = content.replace(old_version_keywords, new_version_keywords)

print("Modified sections:")
print("1. Metadata dictionary - added year and BPM")
print("2. Extraction logic - added year and BPM extraction")
print("3. VERSION_KEYWORDS - added download site words")
print("Writing file...")

with open('C:/Users/home/Documents/DJ/DEV/MusicAnalyzer/audio_analyzer_temp.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Temporary file created: audio_analyzer_temp.py")
