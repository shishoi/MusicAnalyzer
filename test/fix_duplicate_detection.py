"""
Script to fix duplicate detection - add artist mismatch penalty
"""

# Read the audio_analyzer.py file
with open('audio_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the artist match section
old_artist_section = """# Artist match
if item1['artist'] and item2['artist'] and item1['artist'] == item2['artist']:
    factors.append(1.5)  # Strong factor for same artist"""

new_artist_section = """# Artist match/mismatch
if item1['artist'] and item2['artist']:
    if item1['artist'] == item2['artist']:
        factors.append(1.5)  # Strong factor for same artist
    else:
        penalties.append(1.0)  # Penalty for different artists"""

# Check if the old section exists
if old_artist_section in content:
    content = content.replace(old_artist_section, new_artist_section)
    print("✓ Updated artist match logic to include penalty for mismatches")
else:
    print("✗ Could not find the artist match section to replace")
    print("Searching for similar patterns...")
    
    # Try alternate pattern
    import re
    pattern = r"# Artist match.*?factors\.append\(1\.5\).*?# Strong factor for same artist"
    matches = list(re.finditer(pattern, content, re.DOTALL))
    if matches:
        print(f"Found {len(matches)} potential matches")
        for i, match in enumerate(matches):
            print(f"\nMatch {i+1}:")
            print(match.group())
    else:
        print("No matches found. Showing context around 'Artist match':")
        # Find context
        idx = content.find('Artist match')
        if idx >= 0:
            print(content[max(0, idx-100):idx+200])

# Write back
with open('audio_analyzer_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nWrote updated content to: audio_analyzer_fixed.py")
print("Please review the changes before applying them.")
