import os
from mutagen import File as MutagenFile
import librosa
import numpy as np

files = [
    r"C:\Users\home\Documents\DJ\DEV\MusicAnalyzer\test\01 Maman.m4a",
    r"C:\Users\home\Music\15_Hina - חינה\HEBREW REMIX\01 חנניה Gil Lugasy Official Remix.m4a",
    r"C:\Users\home\Music\15_Hina - חינה\MIZRACHIT\01 Terminal 3.m4a",
]

for f in files:
    if not os.path.exists(f):
        print(f"NOT FOUND: {f}")
        continue
    
    print(f"\n{'='*60}")
    print(f"FILE: {os.path.basename(f)}")
    
    # Tag info
    audio = MutagenFile(f)
    tag_br = getattr(audio.info, 'bitrate', 0) or 0
    sr     = getattr(audio.info, 'sample_rate', 0) or 0
    print(f"  Tag bitrate : {tag_br} bps = {tag_br//1000} kbps")
    print(f"  Sample rate : {sr} Hz")
    
    # Spectrum scan — load 8 sec from middle
    duration = audio.info.length
    offset   = duration / 2
    y, sr2 = librosa.load(f, sr=None, offset=offset, duration=8)
    
    n_fft = 4096
    D     = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=n_fft)), ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr2, n_fft=n_fft)
    avg   = np.mean(D, axis=1)
    peak  = np.max(avg)
    
    print(f"  Spectral peak: {peak:.1f} dB")
    
    # Show energy at key frequencies
    for target_hz in [14000, 15000, 16000, 17000, 18000, 19000, 20000, 21000]:
        idx = np.argmin(np.abs(freqs - target_hz))
        print(f"  {target_hz//1000:2d} kHz : {avg[idx]:6.1f} dB  (peak-relative: {avg[idx]-peak:+.1f} dB)")
    
    # Where does content drop 25 dB below peak?
    hf_mask   = freqs >= 10000
    hf_freqs  = freqs[hf_mask]
    hf_spec   = avg[hf_mask]
    threshold = peak - 25
    above     = hf_spec > threshold
    if np.any(above):
        last_idx = np.where(above)[0][-1]
        print(f"  Last freq above (peak-25dB={threshold:.1f}): {hf_freqs[last_idx]:.0f} Hz")
    else:
        print(f"  No HF content above peak-25dB threshold")