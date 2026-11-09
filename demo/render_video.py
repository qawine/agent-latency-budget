#!/usr/bin/env python3
"""Render the captured real terminal output into a 1080x1920 vertical MP4.

The text is exactly demo/expected_output.txt (a real end-to-end run through
Hermes' own plugin loader and hook pipeline) — this script only animates it.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "video"
OUT.mkdir(exist_ok=True)
SRC = HERE / "expected_output.txt"

W, H = 1080, 1920
BG = (11, 12, 18)
CHROME = (22, 23, 32)
FG = (222, 224, 232)
DIM = (130, 133, 148)
ACCENT = (124, 92, 255)
RED = (255, 107, 107)
GREEN = (94, 214, 145)

MONO = "/System/Library/Fonts/Menlo.ttc"
MONO_B = "/System/Library/Fonts/Menlo.ttc"


def font(size: int, bold: bool = False):
    for path in ([MONO_B] if bold else [MONO]):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


FD = font(27)
FD_B = font(27, bold=True)
FT = font(34, bold=True)
FS = font(24)
FY = font(46, bold=True)


def wrap_lines(text: str, width: int = 62):
    out = []
    for raw in text.splitlines():
        if not raw.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(raw, width=width) or [""])
    return out


def render_frame(lines, upto, title, footer):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # chrome
    d.rounded_rectangle((0, 0, W, 120), radius=0, fill=CHROME)
    for i, c in enumerate([(255, 95, 86), (255, 189, 68), (39, 201, 63)]):
        d.ellipse((38 + i * 46, 46, 70 + i * 46, 78), fill=c)
    d.text((200, 44), title, font=FS, fill=DIM)

    y = 176
    for idx, (kind, line) in enumerate(lines):
        if idx > upto:
            break
        color = FG
        f = FD
        if kind == "hdr":
            color, f = ACCENT, FD_B
        elif kind == "bad":
            color, f = RED, FD_B
        elif kind == "good":
            color, f = GREEN, FD_B
        elif kind == "dim":
            color = DIM
        d.text((46, y), line, font=f, fill=color)
        y += 40
        if y > H - 230:
            break

    d.text((46, H - 150), footer, font=FS, fill=DIM)
    d.rounded_rectangle((46, H - 96, W - 46, H - 40), radius=14, fill=(18, 19, 27))
    d.text((70, H - 84), "hermes plugins validate  ✓ safe   ·   PR #151732 open", font=FS, fill=DIM)
    return im


def main() -> int:
    text = SRC.read_text()
    lines = []
    for raw in wrap_lines(text):
        s = raw.rstrip()
        if s.startswith("── "):
            lines.append(("hdr", textwrap.shorten(s, width=60, placeholder="…")))
        elif "verdict" in s or "exceeded" in s or "ok\": false" in s:
            lines.append(("bad", s))
        elif s.strip().startswith('"ok": true') or s.strip().startswith("Validation passed"):
            lines.append(("good", s))
        elif not s.strip():
            lines.append(("gap", ""))
        else:
            lines.append(("dim" if s.startswith(("HERMES_HOME", "config", "plugin ")) else "txt", s))

    lines = [l for l in lines if l[0] != "gap"]
    frames_dir = OUT / "frames"
    frames_dir.mkdir(exist_ok=True)

    title = "~/hermes-agent — demo/e2e_demo.py"
    footer = "real run · Hermes loaded the plugin · real hook pipeline · real tool dispatch"

    total_frames = 0
    # reveal progressively, holding on the interesting lines
    for upto in range(len(lines)):
        base = render_frame(lines, upto, title, footer)
        hold = 1
        k = lines[upto]
        if k[0] in ("hdr", "bad", "good"):
            hold = 14
        elif "2454" in k[1] or "2344" in k[1] or "exceeded" in k[1]:
            hold = 20
        if upto == len(lines) - 1:
            hold = 40
        for _ in range(hold):
            base.save(frames_dir / f"f{total_frames:05d}.png")
            total_frames += 1
    print(f"rendered {total_frames} frames -> {frames_dir}")

    mp4 = OUT / "agent_latency_budget_demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", "12",
        "-i", str(frames_dir / "f%05d.png"),
        "-vf", "format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart",
        str(mp4),
    ], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip()
    print(f"{mp4}  duration={dur}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
