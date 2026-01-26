"""
Fix duplicate detection in audio_analyzer.py
Replace the old similarity calculation with the new penalty-based system
"""

# Read the file
with open('audio_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the old similarity calculation section (lines ~750-780)
old_section = """                # Calculate similarity factors
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
                        processed_in_group.add(item2['path'])"""

new_section = """                # Calculate similarity factors
                factors = []
                penalties = []

                # Duration difference penalty (exact match required within 2 sec)
                duration_diff = abs(item1['duration'] - item2['duration'])
                if duration_diff <= 1.0:
                    dur_factor = 1.0
                elif duration_diff <= 2.0:
                    dur_factor = 0.7  # Minor penalty
                else:
                    penalties.append(0.5)  # Major penalty for > 2 sec difference
                    dur_factor = 0.3
                factors.append(dur_factor)

                # Year mismatch penalty
                if item1['year'] and item2['year']:
                    if item1['year'] != item2['year']:
                        penalties.append(0.7)  # Punish year mismatch

                # BPM mismatch penalty
                if item1['bpm'] and item2['bpm']:
                    bpm_diff = abs(item1['bpm'] - item2['bpm'])
                    if bpm_diff > 1.0:  # Allow 1 BPM tolerance
                        penalties.append(0.7)  # Punish BPM mismatch

                # Similar size factor
                size_ratio = min(item1['size'], item2['size']) / max(item1['size'], item2['size'])
                factors.append(size_ratio * 0.5)  # Reduced weight

                # Similar bitrate factor
                if item1['bitrate'] and item2['bitrate']:
                    bitrate_ratio = min(item1['bitrate'], item2['bitrate']) / max(item1['bitrate'], item2['bitrate'])
                    factors.append(bitrate_ratio * 0.5)  # Reduced weight

                # Title similarity (MORE IMPORTANT than filename)
                if item1['title'] and item2['title']:
                    title_sim = filename_similarity(item1['title'], item2['title'])
                    factors.append(title_sim * 2.0)  # Higher weight for title

                # Filename similarity (LESS IMPORTANT)
                name_sim = filename_similarity(item1['filename'], item2['filename'])
                factors.append(name_sim * 0.8)  # Lower weight for filename

                # Artist match/mismatch
                if item1['artist'] and item2['artist']:
                    if item1['artist'] == item2['artist']:
                        factors.append(1.5)  # Strong factor for same artist
                    else:
                        penalties.append(1.0)  # Penalty for different artists

                # Calculate final score with penalties
                total_score = sum(factors) - sum(penalties)

                # Threshold for considering duplicates
                threshold = 0.8

                if total_score >= threshold:
                    duplicate_group.append(item2['path'])
                    processed_in_group.add(item2['path'])"""

# Replace the section
if old_section in content:
    content = content.replace(old_section, new_section)
    print("✓ Successfully updated duplicate detection logic")
    
    # Write back to file
    with open('audio_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Changes written to audio_analyzer.py")
    print("\nChanges made:")
    print("  - Added duration penalty logic (>2 sec = penalty)")
    print("  - Added year mismatch penalty (0.7)")
    print("  - Added BPM mismatch penalty (0.7 if diff >1 BPM)")
    print("  - Added artist mismatch penalty (1.0)")
    print("  - Increased title weight (2.0x)")
    print("  - Decreased filename weight (0.8x)")
    print("  - Decreased size/bitrate weights (0.5x)")
else:
    print("✗ Could not find the exact section to replace")
    print("\nShowing sections containing 'Calculate similarity':")
    import re
    for match in re.finditer(r'.{0,50}Calculate similarity.{0,200}', content, re.DOTALL):
        print("-" * 80)
        print(match.group())
