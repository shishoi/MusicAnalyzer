#!/usr/bin/env python3
"""Detailed ID3 frame inspection for cover art debugging."""

from mutagen import File
from mutagen.id3 import ID3
import os
import glob

# Target the specific problematic file
test_file = r"Sophie Ellis-Bextor - Murder On The Dancefloor PNAU Remix.mp3"

if not os.path.exists(test_file):
    print(f"File not found: {test_file}")
    print("Scanning for MP3 files...")
    for f in glob.glob("*.mp3"):
        print(f"  Found: {f}")
    exit(1)

print(f"Testing file: {test_file}\n")

# Method 1: Using EasyMP3
print("=" * 80)
print("Method 1: mutagen.File() (EasyMP3)")
print("=" * 80)
audio = File(test_file)
print(f"Type: {type(audio)}")
print(f"Has ID3 attribute: {hasattr(audio, 'ID3')}")
if hasattr(audio, 'ID3'):
    print(f"audio.ID3 type: {type(audio.ID3)}")
    print(f"audio.ID3 is not None: {audio.ID3 is not None}")
    if audio.ID3:
        print(f"Number of frames: {len(audio.ID3)}")
        print("\nAll frames in ID3:")
        for key, frame in audio.ID3.items():
            print(f"  {key}: {type(frame).__name__}")

# Method 2: Direct ID3 access
print("\n" + "=" * 80)
print("Method 2: mutagen.id3.ID3() direct")
print("=" * 80)
try:
    id3 = ID3(test_file)
    print(f"ID3 loaded: {type(id3)}")
    print(f"Number of frames: {len(id3)}")
    print("\nAll frames:")
    for key, frame in id3.items():
        print(f"  {key}: {type(frame).__name__}")
        if key.startswith('APIC'):
            print(f"    -> APIC frame found! Mime type: {frame.mime}")
except Exception as e:
    print(f"Error: {e}")

# Method 3: Check raw keys with string matching
print("\n" + "=" * 80)
print("Method 3: Check frame keys for APIC")
print("=" * 80)
if hasattr(audio, 'ID3') and audio.ID3:
    apic_frames = [k for k in audio.ID3.keys() if 'APIC' in k.upper()]
    print(f"APIC frames found: {apic_frames}")
    if apic_frames:
        print("✓ Cover art detected!")
    else:
        print("✗ No APIC frames found")
else:
    print("✗ No ID3 tag available")

# Method 4: Check if key contains substring 'PIC'
print("\n" + "=" * 80)
print("Method 4: Substring 'PIC' check")
print("=" * 80)
if hasattr(audio, 'ID3') and audio.ID3:
    pic_frames = [k for k in audio.ID3.keys() if 'PIC' in k]
    print(f"Frames containing 'PIC': {pic_frames}")
else:
    print("✗ No ID3 tag available")
