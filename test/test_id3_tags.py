#!/usr/bin/env python3
"""Fix: Check audio.tags instead of audio.ID3"""

from mutagen import File
from mutagen.id3 import ID3
import os

test_file = r"Sophie Ellis-Bextor - Murder On The Dancefloor PNAU Remix.mp3"

print(f"Testing file: {test_file}\n")

# Load with mutagen.File()
audio = File(test_file)
print(f"Type: {type(audio)}")
print(f"audio.ID3: {audio.ID3}")
print(f"audio.tags: {audio.tags}")
print(f"audio.tags type: {type(audio.tags)}")

if audio.tags:
    print(f"\nNumber of frames: {len(audio.tags)}")
    print("\nAll frames:")
    for key, frame in audio.tags.items():
        print(f"  {key}: {type(frame).__name__}")
        
    # Check for APIC
    print("\n" + "=" * 80)
    apic_frames = [k for k in audio.tags.keys() if 'APIC' in k.upper()]
    print(f"APIC frames: {apic_frames}")
    if apic_frames:
        print("✓ Cover art detected!")
    else:
        print("✗ No APIC frames")
