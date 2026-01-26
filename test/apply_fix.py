"""
Fix duplicate detection in audio_analyzer.py  
Replace old similarity calculation with new penalty-based system
"""

with open('audio_analyzer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Print the section we need to replace (lines 750-782)
print("Current code (lines 750-782):")
print(''.join(lines[749:783]))

# We'll create the replacement
print("\n" + "="*80)
print("Creating fixed version...")

new_code = """                # Calculate similarity factors
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
                    processed_in_group.add(item2['path'])

"""

# Replace lines 750-782
new_lines = lines[:750] + [new_code] + lines[783:]

# Write to new file
with open('audio_analyzer_fixed.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Created audio_analyzer_fixed.py with updated duplicate detection")
print("\nTo apply the fix:")
print("  copy audio_analyzer_fixed.py audio_analyzer.py")
