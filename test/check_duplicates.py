import sys
import os
sys.path.insert(0, r'C:\Users\home\Documents\DJ\DEV\MusicAnalyzer')

from audio_analyzer import extract_metadata, normalize_string, strip_version_keywords, filename_similarity

# Analyze the two files
file1 = r'C:\Users\home\Downloads\להיטים חמים 2025\בן חן - יאללה תרקדי.mp3'
file2 = r'C:\Users\home\Downloads\להיטים חמים 2025\סטילה  נס - תיק קטן.mp3'

print("=" * 80)
print("FILE 1: בן חן - יאללה תרקדי.mp3")
print("=" * 80)
metadata1 = extract_metadata(file1)
for key, value in metadata1.items():
    if key != 'path':
        print(f"{key:20s}: {value}")

print("\n" + "=" * 80)
print("FILE 2: סטילה  נס - תיק קטן.mp3")
print("=" * 80)
metadata2 = extract_metadata(file2)
for key, value in metadata2.items():
    if key != 'path':
        print(f"{key:20s}: {value}")

# Calculate similarity factors
print("\n" + "=" * 80)
print("SIMILARITY ANALYSIS")
print("=" * 80)

# Duration difference
duration_diff = abs(metadata1['duration'] - metadata2['duration'])
print(f"Duration difference  : {duration_diff:.2f} seconds")
if duration_diff <= 1.0:
    print("  → PASS: Durations match within 1 second")
elif duration_diff <= 2.0:
    print("  → MINOR PENALTY: Durations differ by 1-2 seconds")
else:
    print("  → MAJOR PENALTY: Durations differ by more than 2 seconds")

# Year mismatch
if metadata1['year'] and metadata2['year']:
    if metadata1['year'] == metadata2['year']:
        print(f"Year                 : {metadata1['year']} = {metadata2['year']} ✓")
    else:
        print(f"Year                 : {metadata1['year']} ≠ {metadata2['year']} → PENALTY")
else:
    print(f"Year                 : Missing data (no penalty)")

# BPM mismatch
if metadata1['bpm'] and metadata2['bpm']:
    bpm_diff = abs(metadata1['bpm'] - metadata2['bpm'])
    if bpm_diff <= 1.0:
        print(f"BPM                  : {metadata1['bpm']:.1f} ≈ {metadata2['bpm']:.1f} ✓")
    else:
        print(f"BPM                  : {metadata1['bpm']:.1f} ≠ {metadata2['bpm']:.1f} (diff: {bpm_diff:.1f}) → PENALTY")
else:
    print(f"BPM                  : Missing data (no penalty)")

# Size similarity
size_ratio = min(metadata1['size'], metadata2['size']) / max(metadata1['size'], metadata2['size'])
print(f"Size ratio           : {size_ratio:.2%}")

# Bitrate similarity
if metadata1['bitrate'] and metadata2['bitrate']:
    bitrate_ratio = min(metadata1['bitrate'], metadata2['bitrate']) / max(metadata1['bitrate'], metadata2['bitrate'])
    print(f"Bitrate ratio        : {bitrate_ratio:.2%}")

# Title similarity
if metadata1['title'] and metadata2['title']:
    title_sim = filename_similarity(metadata1['title'], metadata2['title'])
    print(f"Title similarity     : {title_sim:.2%} (weight: 2.0x)")
    
    # Show normalized titles
    norm_title1 = normalize_string(metadata1['title'])
    norm_title2 = normalize_string(metadata2['title'])
    stripped1 = strip_version_keywords(norm_title1)
    stripped2 = strip_version_keywords(norm_title2)
    print(f"  Normalized title 1 : '{stripped1}'")
    print(f"  Normalized title 2 : '{stripped2}'")
else:
    print(f"Title similarity     : N/A (missing title data)")

# Filename similarity
name_sim = filename_similarity(metadata1['filename'], metadata2['filename'])
print(f"Filename similarity  : {name_sim:.2%} (weight: 0.8x)")

# Show normalized filenames
norm_name1 = normalize_string(metadata1['filename'])
norm_name2 = normalize_string(metadata2['filename'])
stripped_name1 = strip_version_keywords(norm_name1)
stripped_name2 = strip_version_keywords(norm_name2)
print(f"  Normalized name 1  : '{stripped_name1}'")
print(f"  Normalized name 2  : '{stripped_name2}'")

# Artist match
if metadata1['artist'] and metadata2['artist']:
    if metadata1['artist'] == metadata2['artist']:
        print(f"Artist               : '{metadata1['artist']}' = '{metadata2['artist']}' ✓")
    else:
        print(f"Artist               : '{metadata1['artist']}' ≠ '{metadata2['artist']}'")
else:
    print(f"Artist               : Missing data")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("These files should NOT be duplicates if they have:")
print("  - Different artists")
print("  - Different titles (low title similarity)")
print("  - Duration difference > 2 seconds")
print("=" * 80)
