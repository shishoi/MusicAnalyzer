"""
Fix duplicate detection - make title similarity a PRIMARY requirement
Also increase threshold to reduce large duplicate groups
"""

with open('audio_analyzer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the section (around lines 750-800)
old_section = """                # Calculate similarity factors
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

new_section = """                # Calculate title similarity FIRST - this is the PRIMARY requirement
                title_sim = 0.0
                if item1['title'] and item2['title']:
                    title_sim = filename_similarity(item1['title'], item2['title'])
                else:
                    # If no title metadata, use filename similarity
                    title_sim = filename_similarity(item1['filename'], item2['filename'])
                
                # REQUIRE minimum title similarity - skip if titles are too different
                MIN_TITLE_SIMILARITY = 0.70  # Must have at least 70% title match
                if title_sim < MIN_TITLE_SIMILARITY:
                    continue  # Skip this pair - titles are too different
                
                # Calculate similarity factors
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

                # Title similarity (PRIMARY FACTOR - already calculated)
                factors.append(title_sim * 3.0)  # Very high weight for title (increased from 2.0)

                # Filename similarity (LESS IMPORTANT)
                name_sim = filename_similarity(item1['filename'], item2['filename'])
                factors.append(name_sim * 0.5)  # Reduced weight (was 0.8)

                # Artist match/mismatch
                if item1['artist'] and item2['artist']:
                    if item1['artist'] == item2['artist']:
                        factors.append(1.5)  # Strong factor for same artist
                    else:
                        penalties.append(1.0)  # Penalty for different artists

                # Calculate final score with penalties
                total_score = sum(factors) - sum(penalties)

                # Higher threshold to reduce false positives
                threshold = 1.5  # Increased from 0.8

                if total_score >= threshold:
                    duplicate_group.append(item2['path'])
                    processed_in_group.add(item2['path'])
"""

# Read full content
content = ''.join(lines)

# Replace
if old_section in content:
    content = content.replace(old_section, new_section)
    with open('audio_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Successfully updated duplicate detection algorithm")
    print("\nChanges made:")
    print("  1. Title similarity is now a PRIMARY REQUIREMENT (min 70%)")
    print("  2. Files with different titles are immediately skipped")
    print("  3. Title weight increased: 2.0x → 3.0x")
    print("  4. Filename weight decreased: 0.8x → 0.5x")
    print("  5. Threshold increased: 0.8 → 1.5 (stricter matching)")
    print("\nThis should dramatically reduce false positives and group sizes.")
else:
    print("✗ Could not find the section to replace")
    print("The code may have already been modified or has different formatting.")
