#!/usr/bin/env python3
"""Analyze why two songs are being marked as duplicates"""

from mutagen import File as MutagenFile
import os

def analyze_files(file1_path, file2_path):
    """Analyze two files and show their metadata"""
    
    print("=" * 80)
    print("METADATA COMPARISON")
    print("=" * 80)
    
    # Load files
    try:
        f1 = MutagenFile(file1_path)
        f2 = MutagenFile(file2_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        return
    
    # Extract metadata for file 1
    print(f"\nFile 1: {os.path.basename(file1_path)}")
    print("-" * 80)
    print(f"Duration    : {f1.info.length:.2f} seconds")
    print(f"Bitrate     : {f1.info.bitrate} bps ({f1.info.bitrate // 1000} kbps)")
    print(f"Size        : {os.path.getsize(file1_path) / (1024*1024):.2f} MB")
    
    # Title
    title1 = f1.get('TIT2', f1.get('title', ['N/A']))[0] if 'TIT2' in f1 or 'title' in f1 else 'N/A'
    artist1 = f1.get('TPE1', f1.get('artist', ['N/A']))[0] if 'TPE1' in f1 or 'artist' in f1 else 'N/A'
    album1 = f1.get('TALB', f1.get('album', ['N/A']))[0] if 'TALB' in f1 or 'album' in f1 else 'N/A'
    year1 = f1.get('TDRC', f1.get('date', ['N/A']))[0] if 'TDRC' in f1 or 'date' in f1 else 'N/A'
    bpm1 = f1.get('TBPM', f1.get('bpm', ['N/A']))[0] if 'TBPM' in f1 or 'bpm' in f1 else 'N/A'
    
    print(f"Title       : {title1}")
    print(f"Artist      : {artist1}")
    print(f"Album       : {album1}")
    print(f"Year        : {year1}")
    print(f"BPM         : {bpm1}")
    
    # Extract metadata for file 2
    print(f"\nFile 2: {os.path.basename(file2_path)}")
    print("-" * 80)
    print(f"Duration    : {f2.info.length:.2f} seconds")
    print(f"Bitrate     : {f2.info.bitrate} bps ({f2.info.bitrate // 1000} kbps)")
    print(f"Size        : {os.path.getsize(file2_path) / (1024*1024):.2f} MB")
    
    title2 = f2.get('TIT2', f2.get('title', ['N/A']))[0] if 'TIT2' in f2 or 'title' in f2 else 'N/A'
    artist2 = f2.get('TPE1', f2.get('artist', ['N/A']))[0] if 'TPE1' in f2 or 'artist' in f2 else 'N/A'
    album2 = f2.get('TALB', f2.get('album', ['N/A']))[0] if 'TALB' in f2 or 'album' in f2 else 'N/A'
    year2 = f2.get('TDRC', f2.get('date', ['N/A']))[0] if 'TDRC' in f2 or 'date' in f2 else 'N/A'
    bpm2 = f2.get('TBPM', f2.get('bpm', ['N/A']))[0] if 'TBPM' in f2 or 'bpm' in f2 else 'N/A'
    
    print(f"Title       : {title2}")
    print(f"Artist      : {artist2}")
    print(f"Album       : {album2}")
    print(f"Year        : {year2}")
    print(f"BPM         : {bpm2}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    duration_diff = abs(f1.info.length - f2.info.length)
    print(f"\nDuration difference: {duration_diff:.2f} seconds")
    if duration_diff > 2.0:
        print("  → Should apply PENALTY (>2 sec difference)")
    elif duration_diff > 1.0:
        print("  → Should apply minor penalty (1-2 sec difference)")
    else:
        print("  → No penalty (≤1 sec difference)")
    
    if str(year1) != 'N/A' and str(year2) != 'N/A':
        if str(year1) != str(year2):
            print(f"\nYear mismatch: {year1} ≠ {year2}")
            print("  → Should apply PENALTY")
        else:
            print(f"\nYear match: {year1}")
    else:
        print(f"\nYear: Missing data (no penalty)")
    
    if str(bpm1) != 'N/A' and str(bpm2) != 'N/A':
        try:
            bpm1_float = float(str(bpm1))
            bpm2_float = float(str(bpm2))
            bpm_diff = abs(bpm1_float - bpm2_float)
            if bpm_diff > 1.0:
                print(f"\nBPM mismatch: {bpm1} ≠ {bpm2} (diff: {bpm_diff:.1f})")
                print("  → Should apply PENALTY")
            else:
                print(f"\nBPM match: {bpm1} ≈ {bpm2}")
        except:
            print(f"\nBPM: Cannot parse ({bpm1}, {bpm2})")
    else:
        print(f"\nBPM: Missing data (no penalty)")
    
    if str(artist1) != 'N/A' and str(artist2) != 'N/A':
        if str(artist1) != str(artist2):
            print(f"\nArtist mismatch: '{artist1}' ≠ '{artist2}'")
            print("  → Different artists - should NOT be duplicates!")
        else:
            print(f"\nArtist match: '{artist1}'")
    
    if str(title1) != 'N/A' and str(title2) != 'N/A':
        if str(title1) != str(title2):
            print(f"\nTitle mismatch: '{title1}' ≠ '{title2}'")
            print("  → Different titles - should NOT be duplicates!")
        else:
            print(f"\nTitle match: '{title1}'")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    if str(artist1) != str(artist2) or str(title1) != str(title2):
        print("These are DIFFERENT songs and should NOT be marked as duplicates!")
        print("\nPossible reasons for false positive:")
        print("  1. Similar duration might be causing high similarity score")
        print("  2. File size/bitrate similarity")
        print("  3. Filename similarity (if titles are missing)")
        print("  4. Need to increase weight on title/artist match")
    else:
        print("These appear to be the same song (same artist & title)")

def calculate_similarity_score(file1_path, file2_path):
    """Calculate the similarity score as it would be in the duplicate detector"""
    try:
        f1 = MutagenFile(file1_path)
        f2 = MutagenFile(file2_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        return None
    
    # Get metadata
    duration1 = f1.info.length
    duration2 = f2.info.length
    size1 = os.path.getsize(file1_path)
    size2 = os.path.getsize(file2_path)
    bitrate1 = f1.info.bitrate
    bitrate2 = f2.info.bitrate
    
    # Extract tags
    title1 = str(f1.get('TIT2', f1.get('title', ['']))[0] if 'TIT2' in f1 or 'title' in f1 else '')
    title2 = str(f2.get('TIT2', f2.get('title', ['']))[0] if 'TIT2' in f2 or 'title' in f2 else '')
    artist1 = str(f1.get('TPE1', f1.get('artist', ['']))[0] if 'TPE1' in f1 or 'artist' in f1 else '')
    artist2 = str(f2.get('TPE1', f2.get('artist', ['']))[0] if 'TPE1' in f2 or 'artist' in f2 else '')
    year1 = str(f1.get('TDRC', f1.get('date', [None]))[0] if 'TDRC' in f1 or 'date' in f1 else None)
    year2 = str(f2.get('TDRC', f2.get('date', [None]))[0] if 'TDRC' in f2 or 'date' in f2 else None)
    bpm1 = f1.get('TBPM', f1.get('bpm', [None]))[0] if 'TBPM' in f1 or 'bpm' in f1 else None
    bpm2 = f2.get('TBPM', f2.get('bpm', [None]))[0] if 'TBPM' in f2 or 'bpm' in f2 else None
    
    filename1 = os.path.basename(file1_path)
    filename2 = os.path.basename(file2_path)
    
    # Calculate similarity factors (based on FIXED algorithm with artist penalty)
    factors = []
    penalties = []
    
    print("\n" + "=" * 80)
    print("SIMILARITY SCORE CALCULATION (WITH FIX)")
    print("=" * 80)
    
    # Duration difference penalty
    duration_diff = abs(duration1 - duration2)
    if duration_diff <= 1.0:
        dur_factor = 1.0
        print(f"Duration factor: 1.0 (perfect match, diff={duration_diff:.2f}s)")
    elif duration_diff <= 2.0:
        dur_factor = 0.7
        print(f"Duration factor: 0.7 (minor penalty, diff={duration_diff:.2f}s)")
    else:
        penalties.append(0.5)
        dur_factor = 0.3
        print(f"Duration factor: 0.3 + PENALTY 0.5 (major penalty, diff={duration_diff:.2f}s)")
    factors.append(dur_factor)
    
    # Year mismatch penalty
    if year1 and year2 and year1 != 'None' and year2 != 'None':
        if str(year1) != str(year2):
            penalties.append(0.7)
            print(f"Year penalty: 0.7 (year mismatch: {year1} ≠ {year2})")
        else:
            print(f"Year match: {year1}")
    
    # BPM mismatch penalty
    if bpm1 and bpm2:
        try:
            bpm1_float = float(str(bpm1))
            bpm2_float = float(str(bpm2))
            bpm_diff = abs(bpm1_float - bpm2_float)
            if bpm_diff > 1.0:
                penalties.append(0.7)
                print(f"BPM penalty: 0.7 (BPM mismatch: {bpm1} ≠ {bpm2}, diff={bpm_diff:.1f})")
            else:
                print(f"BPM match: {bpm1} ≈ {bpm2}")
        except:
            print(f"BPM: Cannot parse")
    
    # Size similarity
    size_ratio = min(size1, size2) / max(size1, size2)
    size_factor = size_ratio * 0.5
    factors.append(size_factor)
    print(f"Size factor: {size_factor:.3f} (ratio={size_ratio:.3f}, weight=0.5)")
    
    # Bitrate similarity
    if bitrate1 and bitrate2:
        bitrate_ratio = min(bitrate1, bitrate2) / max(bitrate1, bitrate2)
        bitrate_factor = bitrate_ratio * 0.5
        factors.append(bitrate_factor)
        print(f"Bitrate factor: {bitrate_factor:.3f} (ratio={bitrate_ratio:.3f}, weight=0.5)")
    
    # Title similarity (simple check - just compare strings)
    if title1 and title2:
        title_match = 1.0 if title1 == title2 else 0.0
        title_factor = title_match * 2.0
        factors.append(title_factor)
        print(f"Title factor: {title_factor:.3f} (match={title_match}, weight=2.0)")
        print(f"  Title 1: '{title1}'")
        print(f"  Title 2: '{title2}'")
    
    # Filename similarity (simple check)
    filename_match = 1.0 if filename1 == filename2 else 0.0
    filename_factor = filename_match * 0.8
    factors.append(filename_factor)
    print(f"Filename factor: {filename_factor:.3f} (match={filename_match}, weight=0.8)")
    
    # Artist match/mismatch (*** THE FIX ***)
    if artist1 and artist2:
        if artist1 == artist2:
            factors.append(1.5)
            print(f"Artist factor: 1.5 (exact match: '{artist1}')")
        else:
            penalties.append(1.0)  # NEW: Add penalty for different artists!
            print(f"Artist PENALTY: 1.0 (mismatch: '{artist1}' ≠ '{artist2}') *** FIX APPLIED ***")
    
    # Calculate final score
    print(f"\nFactors: {factors}")
    print(f"Penalties: {penalties}")
    
    total_factors = sum(factors)
    total_penalties = sum(penalties)
    
    print(f"\nSum of factors: {total_factors:.3f}")
    print(f"Sum of penalties: {total_penalties:.3f}")
    
    # Apply penalties
    final_score = total_factors - total_penalties
    print(f"\nFinal similarity score: {final_score:.3f}")
    print(f"Threshold: 0.80")
    
    if final_score >= 0.80:
        print("→ Would be classified as DUPLICATE")
    else:
        print("→ Should NOT be classified as duplicate ✓")
    
    return final_score

if __name__ == "__main__":
    file1 = r'C:\Users\home\Downloads\להיטים חמים 2025\בן חן - יאללה תרקדי.mp3'
    file2 = r'C:\Users\home\Downloads\להיטים חמים 2025\סטילה  נס - תיק קטן.mp3'
    
    analyze_files(file1, file2)
    calculate_similarity_score(file1, file2)
