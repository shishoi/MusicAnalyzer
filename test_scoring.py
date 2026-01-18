#!/usr/bin/env python3
"""
Test script to display detailed scoring results for duplicate detection.
Run from command line: python test_scoring.py
"""

import os
import sys
from audio_analyzer import find_duplicate_songs
import mutagen

def get_metadata(file_path):
    """Extract metadata from audio file"""
    try:
        audio = mutagen.File(file_path, easy=True)
        metadata = {
            'filename': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'duration': None,
            'title': None,
            'artist': None,
            'album': None,
            'contrib_artist': None,
        }
        
        if audio is not None and hasattr(audio, "info") and hasattr(audio.info, "length"):
            metadata['duration'] = audio.info.length
        
        if audio is not None:
            if 'title' in audio:
                metadata['title'] = audio['title'][0] if audio['title'] else None
            if 'artist' in audio:
                metadata['artist'] = audio['artist'][0] if audio['artist'] else None
            if 'album' in audio:
                metadata['album'] = audio['album'][0] if audio['album'] else None
            # Contributing artist
            contrib = None
            if 'albumartist' in audio:
                contrib = audio['albumartist'][0] if audio['albumartist'] else None
            elif 'contributingartist' in audio:
                contrib = audio['contributingartist'][0] if audio['contributingartist'] else None
            elif 'performer' in audio:
                contrib = audio['performer'][0] if audio['performer'] else None
            if contrib:
                metadata['contrib_artist'] = contrib
        
        return metadata
    except Exception as e:
        return {'filename': os.path.basename(file_path), 'error': str(e)}


def filename_similarity(name1, name2):
    """Calculate filename similarity (same as in audio_analyzer.py)"""
    name1 = os.path.splitext(name1)[0].lower()
    name2 = os.path.splitext(name2)[0].lower()
    
    try:
        import Levenshtein
        distance = Levenshtein.distance(name1, name2)
        max_len = max(len(name1), len(name2))
        if max_len == 0:
            return 0
        return 1 - (distance / max_len)
    except ImportError:
        common_chars = sum(1 for c in name1 if c in name2)
        max_len = max(len(name1), len(name2))
        if max_len == 0:
            return 0
        return common_chars / max_len


def calculate_group_score(group, tolerance_sec=3.0):
    """Calculate detailed scoring breakdown for a group"""
    n = len(group)
    if n <= 1:
        return None
    
    # Get metadata for all files
    metadata_list = [get_metadata(path) for path in group]
    
    # 1. Filename Similarity (weight: 0.5)
    fname_sim_sum = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i+1, n):
            fname_sim_sum += filename_similarity(
                metadata_list[i]['filename'],
                metadata_list[j]['filename']
            )
            pairs += 1
    fname_sim = (fname_sim_sum / pairs) if pairs else 0.0
    
    # 2. Size consistency (weight: 0.1)
    sizes = [m['size'] for m in metadata_list if 'size' in m]
    size_sim = 0.0
    if len(sizes) >= 2:
        ratios = []
        for i in range(len(sizes)):
            for j in range(i+1, len(sizes)):
                a, b = sizes[i], sizes[j]
                if max(a, b) > 0:
                    ratios.append(min(a, b) / max(a, b))
        if ratios:
            size_sim = sum(ratios) / len(ratios)
    
    # 3. Duration consistency (weight: 0.1)
    durations = [m['duration'] for m in metadata_list if m.get('duration')]
    dur_sim = 0.0
    if durations:
        dur_range = max(durations) - min(durations)
        dur_sim = max(0.0, 1.0 - (dur_range / max(tolerance_sec, 1e-6)))
        if dur_sim > 1.0:
            dur_sim = 1.0
    
    # 4. Title match (weight: 0.1)
    titles = [m['title'].lower() for m in metadata_list if m.get('title')]
    title_factor = 0.0
    if titles:
        from collections import Counter
        c = Counter(titles)
        if c:
            most_common_count = c.most_common(1)[0][1]
            title_factor = most_common_count / len(titles)
    
    # 5. Album match (weight: 0.15)
    albums = [m['album'].lower() for m in metadata_list if m.get('album')]
    album_factor = 0.0
    if albums:
        from collections import Counter
        c = Counter(albums)
        if c:
            most_common_count = c.most_common(1)[0][1]
            album_factor = most_common_count / len(albums)
    
    # 6. Contributing Artist match (weight: 0.15)
    contribs = [m['contrib_artist'].lower() for m in metadata_list if m.get('contrib_artist')]
    contrib_factor = 0.0
    if contribs:
        from collections import Counter
        c = Counter(contribs)
        if c:
            most_common_count = c.most_common(1)[0][1]
            contrib_factor = most_common_count / len(contribs)
    
    # Calculate weighted total score
    total_score = (
        0.5 * fname_sim +
        0.1 * size_sim +
        0.1 * dur_sim +
        0.1 * title_factor +
        0.15 * album_factor +
        0.15 * contrib_factor
    )
    
    return {
        'total_score': total_score,
        'filename_similarity': fname_sim,
        'size_consistency': size_sim,
        'duration_consistency': dur_sim,
        'title_match': title_factor,
        'album_match': album_factor,
        'contrib_artist_match': contrib_factor,
        'metadata': metadata_list
    }


def main():
    """Main test function"""
    test_directory = r"C:\Users\home\Documents\DJ\DEV\MusicAnalyzer"
    
    print("=" * 80)
    print("DUPLICATE DETECTION SCORING TEST")
    print("=" * 80)
    print(f"\nScanning directory: {test_directory}")
    print("\nScoring weights:")
    print("  • Filename Similarity:      50%")
    print("  • Album Match:              15%")
    print("  • Contributing Artist:      15%")
    print("  • File Size Consistency:    10%")
    print("  • Duration Consistency:     10%")
    print("  • Title Match:              10%")
    print("=" * 80)
    
    # Find duplicates
    print("\nSearching for duplicates...\n")
    duplicates = find_duplicate_songs(test_directory, tolerance_sec=3.0)
    
    if not duplicates:
        print("\nNo duplicate groups found.")
        return
    
    print(f"\n\nFound {len(duplicates)} duplicate groups")
    print("=" * 80)
    
    # Display each group with detailed scoring
    for i, group in enumerate(duplicates):
        print(f"\n{'='*80}")
        print(f"GROUP {i+1} ({len(group)} files)")
        print('='*80)
        
        # Calculate scores
        scores = calculate_group_score(group)
        
        if scores:
            print(f"\n📊 SCORING BREAKDOWN:")
            print(f"  Total Score:              {scores['total_score']:.3f}")
            print(f"  ├─ Filename Similarity:   {scores['filename_similarity']:.3f} (weight: 50%)")
            print(f"  ├─ Album Match:           {scores['album_match']:.3f} (weight: 15%)")
            print(f"  ├─ Artist Match:          {scores['contrib_artist_match']:.3f} (weight: 15%)")
            print(f"  ├─ Size Consistency:      {scores['size_consistency']:.3f} (weight: 10%)")
            print(f"  ├─ Duration Consistency:  {scores['duration_consistency']:.3f} (weight: 10%)")
            print(f"  └─ Title Match:           {scores['title_match']:.3f} (weight: 10%)")
            
            print(f"\n📁 FILES IN GROUP:")
            for j, (path, meta) in enumerate(zip(group, scores['metadata'])):
                print(f"\n  [{j+1}] {meta['filename']}")
                print(f"      Path: {path}")
                if meta.get('title'):
                    print(f"      Title: {meta['title']}")
                if meta.get('artist'):
                    print(f"      Artist: {meta['artist']}")
                if meta.get('album'):
                    print(f"      Album: {meta['album']}")
                if meta.get('contrib_artist'):
                    print(f"      Contributing Artist: {meta['contrib_artist']}")
                if meta.get('duration'):
                    mins = int(meta['duration'] // 60)
                    secs = int(meta['duration'] % 60)
                    print(f"      Duration: {mins}:{secs:02d}")
                if meta.get('size'):
                    size_mb = meta['size'] / (1024 * 1024)
                    print(f"      Size: {size_mb:.2f} MB")
    
    print("\n" + "="*80)
    print("END OF SCORING REPORT")
    print("="*80)


if __name__ == "__main__":
    main()
