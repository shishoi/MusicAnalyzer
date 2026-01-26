"""Analyze why two completely different songs are marked as duplicates"""
from mutagen import File as MutagenFile
import os

file1_path = r'C:\Users\home\Music\NEW-חדש-למיין\SHMONIM Disco Edit אושר כהן - ככה וככהVIP Djs.mp3'
file2_path = r'C:\Users\home\Music\NEW-חדש-למיין\עומר_אדם_טמפרטורה_NBD__Tzach_Ziv_Intro_Edit_Fm_98.mp3'

try:
    f1 = MutagenFile(file1_path)
    f2 = MutagenFile(file2_path)
    
    print("=" * 80)
    print("FALSE POSITIVE ANALYSIS")
    print("=" * 80)
    
    print(f"\nFile 1: {os.path.basename(file1_path)}")
    print("-" * 80)
    print(f"Duration    : {f1.info.length:.2f} seconds")
    print(f"Bitrate     : {f1.info.bitrate} bps ({f1.info.bitrate // 1000} kbps)")
    print(f"Size        : {os.path.getsize(file1_path) / (1024*1024):.2f} MB")
    
    title1 = str(f1.get('TIT2', f1.get('title', ['N/A']))[0] if 'TIT2' in f1 or 'title' in f1 else 'N/A')
    artist1 = str(f1.get('TPE1', f1.get('artist', ['N/A']))[0] if 'TPE1' in f1 or 'artist' in f1 else 'N/A')
    year1 = str(f1.get('TDRC', f1.get('date', [None]))[0] if 'TDRC' in f1 or 'date' in f1 else None)
    bpm1 = f1.get('TBPM', f1.get('bpm', [None]))[0] if 'TBPM' in f1 or 'bpm' in f1 else None
    
    print(f"Title       : {title1}")
    print(f"Artist      : {artist1}")
    print(f"Year        : {year1}")
    print(f"BPM         : {bpm1}")
    
    print(f"\nFile 2: {os.path.basename(file2_path)}")
    print("-" * 80)
    print(f"Duration    : {f2.info.length:.2f} seconds")
    print(f"Bitrate     : {f2.info.bitrate} bps ({f2.info.bitrate // 1000} kbps)")
    print(f"Size        : {os.path.getsize(file2_path) / (1024*1024):.2f} MB")
    
    title2 = str(f2.get('TIT2', f2.get('title', ['N/A']))[0] if 'TIT2' in f2 or 'title' in f2 else 'N/A')
    artist2 = str(f2.get('TPE1', f2.get('artist', ['N/A']))[0] if 'TPE1' in f2 or 'artist' in f2 else 'N/A')
    year2 = str(f2.get('TDRC', f2.get('date', [None]))[0] if 'TDRC' in f2 or 'date' in f2 else None)
    bpm2 = f2.get('TBPM', f2.get('bpm', [None]))[0] if 'TBPM' in f2 or 'bpm' in f2 else None
    
    print(f"Title       : {title2}")
    print(f"Artist      : {artist2}")
    print(f"Year        : {year2}")
    print(f"BPM         : {bpm2}")
    
    # Calculate title similarity using rapidfuzz
    from rapidfuzz import fuzz
    
    # Use title if available, otherwise use filename
    if title1 != 'N/A' and title2 != 'N/A':
        title_sim = fuzz.token_set_ratio(title1, title2) / 100.0
        print(f"\n" + "=" * 80)
        print(f"TITLE SIMILARITY (PRIMARY CHECK)")
        print("=" * 80)
        print(f"Title 1: '{title1}'")
        print(f"Title 2: '{title2}'")
        print(f"Similarity: {title_sim:.2%}")
        print(f"Minimum required: 70%")
        
        if title_sim < 0.70:
            print(f"\n✓ Should be SKIPPED (title similarity {title_sim:.2%} < 70%)")
        else:
            print(f"\n✗ Would PASS title check (similarity {title_sim:.2%} >= 70%)")
    else:
        # Fall back to filename comparison
        filename_sim = fuzz.token_set_ratio(os.path.basename(file1_path), os.path.basename(file2_path)) / 100.0
        print(f"\n" + "=" * 80)
        print(f"FILENAME SIMILARITY (No title metadata)")
        print("=" * 80)
        print(f"Filename 1: '{os.path.basename(file1_path)}'")
        print(f"Filename 2: '{os.path.basename(file2_path)}'")
        print(f"Similarity: {filename_sim:.2%}")
        print(f"Minimum required: 70%")
        
        if filename_sim < 0.70:
            print(f"\n✓ Should be SKIPPED (filename similarity {filename_sim:.2%} < 70%)")
        else:
            print(f"\n✗ Would PASS filename check (similarity {filename_sim:.2%} >= 70%)")
    
    # Check other differences
    print(f"\n" + "=" * 80)
    print("OTHER CHECKS")
    print("=" * 80)
    
    duration_diff = abs(f1.info.length - f2.info.length)
    print(f"Duration difference: {duration_diff:.2f} seconds")
    if duration_diff > 2.0:
        print(f"  → Would apply major penalty (>2 sec)")
    
    if artist1 != 'N/A' and artist2 != 'N/A' and artist1 != artist2:
        print(f"Artist mismatch: '{artist1}' ≠ '{artist2}'")
        print(f"  → Would apply 1.0 penalty")
    
    if year1 and year2 and year1 != 'None' and year2 != 'None' and year1 != year2:
        print(f"Year mismatch: {year1} ≠ {year2}")
        print(f"  → Would apply 0.7 penalty")
    
    if bpm1 and bpm2:
        try:
            bpm_diff = abs(float(str(bpm1)) - float(str(bpm2)))
            if bpm_diff > 1.0:
                print(f"BPM mismatch: {bpm1} ≠ {bpm2} (diff: {bpm_diff:.1f})")
                print(f"  → Would apply 0.7 penalty")
        except:
            pass
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("These files should NOT be marked as duplicates because:")
    print("  - Different titles (or low title similarity)")
    print("  - Different artists")
    print("  - Different metadata")
    print("\nIf they ARE being matched, there's a bug in the algorithm.")
    print("=" * 80)

except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
