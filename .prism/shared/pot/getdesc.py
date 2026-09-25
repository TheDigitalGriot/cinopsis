import sys, io, os
sys.stdout.reconfigure(encoding='utf-8')
import yt_dlp
VID = sys.argv[1]
OUT = sys.argv[2]
opts = {"quiet": True, "no_warnings": True, "skip_download": True,
        "writesubtitles": False, "writeautomaticsub": False,
        "extract_flat": False, "noplaylist": True}
with yt_dlp.YoutubeDL(opts) as y:
    info = y.extract_info(f"https://www.youtube.com/watch?v={VID}", download=False)
title = info.get("title") or ""
dur = int(info.get("duration") or 0)
desc = (info.get("description") or "").strip()
chan = info.get("uploader") or info.get("channel") or ""
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(f"{title} | len={dur}s\n")
    f.write(desc + "\n")
print("TITLE:", title)
print("CHANNEL:", chan)
print("DURATION:", dur)
print("DESC_CHARS:", len(desc))
print("DESC_HEAD:", desc[:600].replace("\n", " | "))
print("WROTE:", OUT)
