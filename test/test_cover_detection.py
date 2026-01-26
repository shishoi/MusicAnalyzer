#!/usr/bin/env python3
"""
Test script to debug cover art detection
"""

import os
import mutagen
from mutagen.id3 import ID3

def check_cover_art(file_path):
    """Check for cover art in various formats"""
    print(f"\n{'='*80}")
    print(f"Checking: {os.path.basename(file_path)}")
    print('='*80)
    
    try:
        audio = mutagen.File(file_path, easy=True)
        print(f"\nFile loaded successfully")
        print(f"Type: {type(audio)}")
        
        if audio is None:
            print("Audio is None!")
            return 0
        
        # Check available attributes
        print(f"\nAudio attributes: {dir(audio)}")
        
        # Try different detection methods
        has_cover = 0
        
        # Method 1: ID3v2 pictures (MP3)
        print("\n1. Checking ID3v2 pictures...")
        try:
            id3 = ID3(file_path)
            apic_frames = [frame for frame in id3.values() if frame.FrameID.startswith('APIC')]
            if apic_frames:
                print(f"   ✓ Found {len(apic_frames)} APIC frames (ID3 pictures)")
                has_cover = 1
            else:
                print("   ✗ No APIC frames found")
        except Exception as e:
            print(f"   ✗ ID3 check failed: {e}")
        
        # Method 2: Check .pictures attribute
        print("\n2. Checking .pictures attribute...")
        if hasattr(audio, 'pictures'):
            print(f"   Has 'pictures' attribute: {bool(audio.pictures)}")
            if audio.pictures:
                print(f"   ✓ Found {len(audio.pictures)} pictures")
                has_cover = 1
            else:
                print("   ✗ pictures list is empty")
        else:
            print("   ✗ No 'pictures' attribute")
        
        # Method 3: Check metadata_block_picture (Vorbis)
        print("\n3. Checking metadata_block_picture (Vorbis)...")
        if hasattr(audio, 'get'):
            if 'metadata_block_picture' in audio:
                print("   ✓ Found metadata_block_picture")
                has_cover = 1
            else:
                print("   ✗ No metadata_block_picture")
        
        # Method 4: Check covr (MP4/M4A)
        print("\n4. Checking covr (MP4)...")
        if hasattr(audio, 'get'):
            if 'covr' in audio:
                print("   ✓ Found covr tag")
                has_cover = 1
            else:
                print("   ✗ No covr tag")
        
        # Method 5: Direct tag inspection
        print("\n5. Direct tag inspection...")
        print(f"   Available tags: {list(audio.tags.keys()) if audio.tags else 'No tags'}")
        
        # Look for any picture-related tags
        picture_tags = [tag for tag in audio.tags.keys() if 'picture' in tag.lower() or 'apic' in tag.lower() or 'covr' in tag.lower()]
        if picture_tags:
            print(f"   ✓ Found picture-related tags: {picture_tags}")
            has_cover = 1
        
        print(f"\n{'='*80}")
        print(f"FINAL RESULT: has_cover = {has_cover}")
        print('='*80)
        return has_cover
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Scan directory for audio files and check covers"""
    directory = r"C:\Users\home\Documents\DJ\DEV\MusicAnalyzer"
    
    print("Scanning directory for audio files...")
    audio_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg')):
                full_path = os.path.join(root, file)
                audio_files.append(full_path)
    
    print(f"Found {len(audio_files)} audio files\n")
    
    # Check first 5 files
    for file_path in audio_files[:5]:
        check_cover_art(file_path)


if __name__ == "__main__":
    main()
