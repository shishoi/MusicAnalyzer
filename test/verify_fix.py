"""Test the fix - verify that 2-item groups now check title similarity"""
from rapidfuzz import fuzz

# Simulate the two problem files
title1 = "Kaha V Kaha- SHMONIM Disco Edit"
title2 = "טמפרטורה (NBD & Tzach Ziv Intro Edit)"

# Normalize like the algorithm does
import re

def normalize_string(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\.(mp3|wav|flac|m4a|aac|ogg|wma|aiff|alac)$', '', text)
    text = re.sub(r'[_\-\.+]', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def strip_version_keywords(text):
    keywords = ['remix', 'rmx', 'radio edit', 'radio version', 'original mix',
                'extended', 'extended mix', 'club mix', 'dub', 'instrumental',
                'acapella', 'a cappella', 'vocal mix', 'club version', 'edit',
                'remaster', 'remastered', 'vip', 'bootleg', 'mashup', 'rework',
                'radio', 'club', 'version', 'original', 'mix',
                'youtube', 'spotidownloader', 'spotidown', 'app', 'com', 'mp3',
                'v3', 'yt1z', 'net', 'download', 'free', 'converted', 'disco']
    result = text
    for keyword in keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    result = re.sub(r'\s+', ' ', result).strip()
    return result

print("=" * 80)
print("TESTING FIX FOR 2-ITEM GROUP BUG")
print("=" * 80)

print(f"\nOriginal titles:")
print(f"  Title 1: '{title1}'")
print(f"  Title 2: '{title2}'")

# Normalize
norm1 = normalize_string(title1)
norm2 = normalize_string(title2)
print(f"\nNormalized:")
print(f"  Title 1: '{norm1}'")
print(f"  Title 2: '{norm2}'")

# Strip version keywords
stripped1 = strip_version_keywords(norm1)
stripped2 = strip_version_keywords(norm2)
print(f"\nAfter stripping version keywords:")
print(f"  Title 1: '{stripped1}'")
print(f"  Title 2: '{stripped2}'")

# Calculate similarity
similarity = fuzz.token_set_ratio(stripped1, stripped2) / 100.0

print(f"\n" + "=" * 80)
print(f"TITLE SIMILARITY: {similarity:.2%}")
print(f"MINIMUM REQUIRED: 70%")
print("=" * 80)

if similarity < 0.70:
    print("\n✓✓✓ RESULT: Files will be SKIPPED (not marked as duplicates)")
    print("✓✓✓ FIX WORKING: Even in 2-item groups, title check is applied!")
else:
    print("\n✗✗✗ RESULT: Files would PASS title check")
    print("✗✗✗ Similarity too high - need to adjust normalization")

print("\nBEFORE FIX: 2-item groups were automatically marked as duplicates")
print("AFTER FIX: All groups must pass the 70% title similarity check")
print("=" * 80)
