from mutagen import File
fn = r"Aqua - Barbie Girl (Official Music Video).mp3"
a = File(fn)
print("type:", type(a))
print("has tags:", bool(getattr(a,'tags',None)))
ks = list(getattr(a,'tags',{}).keys())
print("APIC keys:", [k for k in ks if 'APIC' in k])
frames = []
for k in ks:
    if 'APIC' in k:
        f = a.tags.get(k)
        frames.append((k, getattr(f,'mime',None), len(getattr(f,'data',b''))))
print("frames:", frames)
