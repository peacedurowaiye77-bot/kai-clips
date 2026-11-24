"""Snapshot a live Twitch VOD's audio playlist as a finished one and download it fast."""
import subprocess, sys, urllib.request, urllib.parse, pathlib
url, work = sys.argv[1], pathlib.Path(sys.argv[2])
m3u8 = subprocess.run(["yt-dlp", "-g", "-f", "ba/wa/w", url], capture_output=True, text=True, check=True).stdout.strip().splitlines()[0]
text = urllib.request.urlopen(m3u8, timeout=30).read().decode()
out = []
for line in text.splitlines():
    if line and not line.startswith("#"):
        line = urllib.parse.urljoin(m3u8, line)
    elif line.startswith("#EXT-X-PLAYLIST-TYPE"):
        line = "#EXT-X-PLAYLIST-TYPE:VOD"
    elif line.startswith('#EXT-X-MAP:URI="'):
        uri = line.split('"')[1]
        line = line.replace(uri, urllib.parse.urljoin(m3u8, uri))
    out.append(line)
if "#EXT-X-ENDLIST" not in text:
    out.append("#EXT-X-ENDLIST")
pl = work / "frozen.m3u8"
pl.write_text("\n".join(out) + "\n")
segs = sum(1 for l in out if l and not l.startswith("#"))
print(f"{segs} segments", flush=True)
subprocess.run(["yt-dlp", "--enable-file-urls", "-N", "16", "-o", str(work / "audio.%(ext)s"),
                pl.resolve().as_uri()], check=True, capture_output=True, text=True)
pl.unlink()
