#!/usr/bin/env python3
"""Quick test of the fixed cover detection."""

from mutagen import File

test_file = r"Sophie Ellis-Bextor - Murder On The Dancefloor PNAU Remix.mp3"

audio = File(test_file)
meta = {'has_cover': 0}

try:
    if audio is not None:
        has_picture = False
        # Check ID3v2 APIC frames (MP3)
        if hasattr(audio, 'tags') and audio.tags is not None:
            for key in audio.tags.keys():
                if 'APIC' in key:
                    has_picture = True
                    break
        # Vorbis comments (FLAC, OGG)
        elif 'metadata_block_picture' in audio:
            has_picture = True
        # MP4 cover art
        elif 'covr' in audio:
            has_picture = True
        meta['has_cover'] = 1 if has_picture else 0
except Exception as e:
    meta['has_cover'] = 0
    print(f"Error: {e}")

print(f"File: {test_file}")
print(f"has_cover result: {meta['has_cover']}")
print(f"Expected: 1")
print(f"Success: {meta['has_cover'] == 1}")
