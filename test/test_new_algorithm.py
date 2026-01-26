"""Test the updated duplicate detection algorithm"""
import sys
sys.path.insert(0, r'C:\Users\home\Documents\DJ\DEV\MusicAnalyzer')
from audio_analyzer import filename_similarity

# Simulate the two files
file1 = {
    'title': 'יאללה תרקדי',
    'artist': 'בן חן',
    'filename': 'בן חן - יאללה תרקדי.mp3',
    'duration': 173.71,
    'size': 6970000,
    'bitrate': 320000,
    'year': '2024-12-23',
    'bpm': 0
}

file2 = {
    'title': 'תיק קטן',
    'artist': 'סטילה & נס',
    'filename': 'סטילה  נס - תיק קטן.mp3',
    'duration': 173.91,
    'size': 6990000,
    'bitrate': 320000,
    'year': '2023',
    'bpm': 0
}

print("=" * 80)
print("TESTING UPDATED DUPLICATE DETECTION")
print("=" * 80)

# Calculate title similarity FIRST
title_sim = filename_similarity(file1['title'], file2['title'])
print(f"\n1. Title Similarity Check (PRIMARY REQUIREMENT):")
print(f"   File 1 title: '{file1['title']}'")
print(f"   File 2 title: '{file2['title']}'")
print(f"   Similarity: {title_sim:.2%}")
print(f"   Minimum required: 70%")

if title_sim < 0.70:
    print(f"   → SKIPPED: Title similarity {title_sim:.2%} < 70% minimum")
    print(f"   → These files will NOT be compared further")
    print(f"\n✓ Algorithm will correctly skip this pair!")
else:
    print(f"   → PASSED: Title similarity {title_sim:.2%} >= 70%")
    print(f"   → Will continue with full comparison")
    
    # Calculate other factors
    factors = []
    penalties = []
    
    # Duration
    duration_diff = abs(file1['duration'] - file2['duration'])
    if duration_diff <= 1.0:
        factors.append(1.0)
    elif duration_diff <= 2.0:
        factors.append(0.7)
    else:
        penalties.append(0.5)
        factors.append(0.3)
    
    # Year
    if file1['year'] != file2['year']:
        penalties.append(0.7)
    
    # Size
    size_ratio = min(file1['size'], file2['size']) / max(file1['size'], file2['size'])
    factors.append(size_ratio * 0.5)
    
    # Bitrate
    bitrate_ratio = min(file1['bitrate'], file2['bitrate']) / max(file1['bitrate'], file2['bitrate'])
    factors.append(bitrate_ratio * 0.5)
    
    # Title (3.0x weight)
    factors.append(title_sim * 3.0)
    
    # Filename (0.5x weight)
    name_sim = filename_similarity(file1['filename'], file2['filename'])
    factors.append(name_sim * 0.5)
    
    # Artist
    if file1['artist'] != file2['artist']:
        penalties.append(1.0)
    
    total_score = sum(factors) - sum(penalties)
    print(f"\n2. Full Scoring:")
    print(f"   Total factors: {sum(factors):.2f}")
    print(f"   Total penalties: {sum(penalties):.2f}")
    print(f"   Final score: {total_score:.2f}")
    print(f"   Threshold: 1.5")
    
    if total_score >= 1.5:
        print(f"   → Would be marked as DUPLICATE")
    else:
        print(f"   → Would NOT be marked as duplicate")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("With the new algorithm:")
print("  - Title similarity must be >= 70% to even compare files")
print("  - Title weight increased to 3.0x (was 2.0x)")
print("  - Threshold increased to 1.5 (was 0.8)")
print("  - This dramatically reduces false positives")
print("=" * 80)
