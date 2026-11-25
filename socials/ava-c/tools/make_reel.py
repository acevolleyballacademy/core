#!/usr/bin/env python3
"""Cut a Reel/TikTok from a full match video (16:9 baseline camera).

Default: landscape 1920x1080, full frame. --vertical: 1080x1920 with the court in the middle and
a blurred fill above/below.
Highlights get the yellow HIGHLIGHTS label. Lowlights get no label, only the --hook text.

  python3 make_reel.py MATCH.mp4 START END --type highlight --hook "we have our moments 🔥" \
      [--slow 1:02:13.5-1:02:15.0] [--out reel.mp4]

Times: seconds (3733.5) or h:mm:ss(.s) / mm:ss(.s).
--slow: replay this part of the clip again at 40% speed after the full-speed play.
--zoom: crop factor for the centre video (1.0 = whole frame, 1.4 = zoom into the middle).
Needs ffmpeg. Original video is never changed.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
import os, shutil
FFMPEG = os.environ.get("AVACLIPS_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
ASSETS = HERE.parent / "assets"
OVERLAYS = {
    "highlight": ASSETS / "overlay_highlight.png",
    "lowlight": ASSETS / "overlay_lowlight.png",  # logo only, no label
    "benchcam": ASSETS / "overlay_benchcam.png",
    "playerqs": ASSETS / "overlay_player_qs.png",
    "none": None,
}
W, H = 1920, 1080  # set by --vertical


def _font_dir():
    """Inter Display lives in different places on Linux / the Mac (AVA Stats ships it)."""
    import os, glob
    cands = [os.environ.get("AVA_FONT_DIR", ""), "/usr/share/fonts/opentype/inter",
             str(Path.home() / "Library/Fonts"), "/Library/Fonts"]
    cands += glob.glob(str(Path.home() / "**/video/app/assets/fonts"), recursive=False)
    cands += glob.glob(str(Path.home() / "*/video/app/assets/fonts")) + glob.glob(str(Path.home() / "*/*/video/app/assets/fonts"))
    for c in cands:
        if c and Path(c, "InterDisplay-Black.otf").exists() or (c and Path(c, "InterDisplay-BlackItalic.otf").exists()):
            return Path(c)
    sys.exit("Inter Display font not found. Set AVA_FONT_DIR to a folder with InterDisplay-*.otf")


def _font():
    d = _font_dir()
    for n in ("InterDisplay-Black.otf", "InterDisplay-BlackItalic.otf"):
        if (d / n).exists():
            return str(d / n)


def t(s: str) -> float:
    parts = [float(p) for p in s.split(":")]
    v = 0.0
    for p in parts:
        v = v * 60 + p
    return v


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])


def segment(src, start, end, out, speed, zoom, hook, overlay):
    dur = end - start
    cw = f"iw/{zoom}"
    ch = f"ih/{zoom}"
    if W > H:  # landscape: full frame, no fill
        vf = (f"[0:v]crop={cw}:{ch},scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2[v0]")
    else:
        vf = (
            f"[0:v]crop={cw}:{ch},split[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.12[bg];"
            f"[b]scale={W}:-2:flags=lanczos[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v0]"
        )
    last = "v0"
    inputs = ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src)]
    if overlay:
        inputs += ["-i", str(overlay)]
        vf += f";[1:v]scale={W}:{H}[ov];[{last}][ov]overlay=0:0[v1]"
        last = "v1"
    if hook:
        hook_file = Path(out).with_suffix(".hook.txt")
        hook_file.write_text(hook, encoding="utf-8")
        vf += (f";[{last}]drawtext=fontfile={_font()}:textfile={hook_file}:fontsize={72 if W > H else 64}:fontcolor=white:"
               f"borderw=7:bordercolor=black:x=(w-text_w)/2:y=h*{0.82 if W > H else 0.72}[v2]")
        last = "v2"
    if speed != 1.0:
        vf += f";[{last}]setpts=PTS/{speed}[v3]"
        last = "v3"
        af = f"atempo={max(speed, 0.5)}" + (",atempo=0.8" if speed < 0.5 else "")
    else:
        af = "anull"
    vf += f";[{last}]fps=30,format=yuv420p[vout]"
    run([FFMPEG, "-y", *inputs, "-filter_complex", vf, "-map", "[vout]", "-map", "0:a?",
         "-af", af, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(out)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("start")
    ap.add_argument("end")
    ap.add_argument("--type", choices=OVERLAYS, default="highlight")
    ap.add_argument("--hook", default="")
    ap.add_argument("--slow", help="START-END inside the clip to replay at 40%% speed")
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--vertical", action="store_true", help="9:16 instead of landscape 16:9")
    ap.add_argument("--out")
    a = ap.parse_args()
    global W, H
    if a.vertical:
        W, H = 1080, 1920

    src = Path(a.video)
    start, end = t(a.start), t(a.end)
    out = Path(a.out) if a.out else src.with_name(f"{src.stem}_{a.type}_{int(start)}.mp4")
    ov = OVERLAYS[a.type]
    if ov and not a.vertical:
        land = ov.with_name(ov.stem + "_landscape.png")
        ov = land if land.exists() else None

    with tempfile.TemporaryDirectory() as tmp:
        parts = [Path(tmp) / "p1.mp4"]
        segment(src, start, end, parts[0], 1.0, a.zoom, a.hook, ov)
        if a.slow:
            s0, s1 = (t(x) for x in a.slow.split("-"))
            parts.append(Path(tmp) / "p2.mp4")
            segment(src, s0, s1, parts[1], 0.4, a.zoom * 1.25, "", ov)
        lst = Path(tmp) / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
             "-movflags", "+faststart", str(out)])
    print(out)


if __name__ == "__main__":
    main()
