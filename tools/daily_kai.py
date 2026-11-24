#!/usr/bin/env python3
"""Daily fresh clips: find Kai Cenat's newest GTA stream on Twitch, clip the hours not
clipped yet, and put the new clips at the FRONT of queue.json (best score first).

Run with the clipper's own Python:  ~/.gta6-clipper/venv/bin/python tools/daily_kai.py
State (how far each stream has been clipped) lives in state.json in this repo.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
VENV_BIN = Path.home() / ".gta6-clipper" / "venv" / "bin"
CLIPPER = Path.home() / ".claude" / "skills" / "gta6-clipper" / "scripts" / "gta6clip"
WORK = Path.home() / "gta6-clips" / "work"
CHANNEL = "https://www.twitch.tv/kaicenat/videos?filter=archives&sort=time"
CLIPS_PER_RUN = 4
MAX_SECTION = 10 * 3600      # clip at most 10 hours of stream per run
MIN_NEW = 20 * 60            # ignore less than 20 new minutes

env = dict(os.environ, PATH=f"{VENV_BIN}:{os.environ['PATH']}")


def sh(cmd, **kw):
    return subprocess.run(cmd, env=env, capture_output=True, text=True, **kw)


def hms(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def main():
    state_path = REPO / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    out = sh(["yt-dlp", "--flat-playlist", "--playlist-end", "5",
              "--print", "%(id)s|%(title)s", CHANNEL], timeout=120).stdout
    vods = [l.split("|", 1) for l in out.splitlines() if "|" in l]
    vods = [(v, t) for v, t in vods if "gta" in t.lower()]
    if not vods:
        print("RESULT: no recent Kai Cenat GTA streams found on Twitch")
        return

    for vid, title in vods:                       # newest first
        num = vid.lstrip("v")
        url = f"https://www.twitch.tv/videos/{num}"
        info = json.loads(sh(["yt-dlp", "-J", url], timeout=180).stdout or "{}")
        length = float(info.get("duration") or 0)
        done = float(state.get(vid, {}).get("done_to", 0))
        if length - done < MIN_NEW:
            continue
        lo, hi = done, min(length, done + MAX_SECTION)
        print(f"STREAM: {title} ({vid}), clipping {hms(lo)}-{hms(hi)} of {hms(length)}")

        work = WORK / f"www_twitch_tv_videos_{num}"
        work.mkdir(parents=True, exist_ok=True)
        for f in work.glob("audio.*"):            # a live stream grows: always refetch
            f.unlink()
        r = sh([str(VENV_BIN / "python"), "-I", str(TOOLS / "freeze_audio.py"), url, str(work)],
               timeout=3600)
        if r.returncode != 0:
            print("RESULT: audio download failed:", (r.stderr or r.stdout)[-400:])
            return
        r = sh(["bash", str(CLIPPER), url, "--clips", str(CLIPS_PER_RUN),
                "--section", f"{hms(lo)}-{hms(hi)}"], timeout=4 * 3600, cwd=str(Path.home()))
        log = r.stdout + r.stderr
        m = re.findall(r"(/root/gta6-clips/\d{4}-\d\d-\d\d/[^\s]+)", log)
        if not m:
            print("RESULT: clipping produced no clips. Last lines:\n" + "\n".join(log.splitlines()[-15:]))
            return
        outdir = Path(m[-1])
        clips = json.loads((outdir / "clips.json").read_text())["clips"]

        queue = json.loads((REPO / "queue.json").read_text())
        fresh = []
        stamp = date.today().strftime("%m%d")
        for i, c in enumerate(sorted(clips, key=lambda c: -(c.get("score") or 0)), 1):
            name = f"f{stamp}_{i}_{re.sub(r'^\d\d_', '', c['file'])}"
            shutil.copy(outdir / c["file"], REPO / "queue" / name)
            caption = (c.get("caption") or "").strip()
            tags = " ".join(c.get("hashtags") or [])
            fresh.append({"file": f"queue/{name}", "hook": c["hook_text"],
                          "caption": f"{caption}\n\n{tags}".strip(), "score": c.get("score")})
        (REPO / "queue.json").write_text(json.dumps(fresh + queue, indent=2, ensure_ascii=False))
        state[vid] = {"title": title, "done_to": hi, "length_seen": length}
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        for f in work.glob("audio.*"):
            f.unlink()
        print(f"RESULT: added {len(fresh)} fresh clip(s) to the front of the queue:")
        for f in fresh:
            print(f"  [{f['score']}] {f['hook']}")
        return

    print("RESULT: no new Kai Cenat GTA stream time since the last run")


if __name__ == "__main__":
    sys.exit(main())
