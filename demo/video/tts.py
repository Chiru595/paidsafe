"""Generate one narration clip per scene with Edge neural TTS and report durations.

    python demo/video/tts.py <work_dir>
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

import edge_tts
import imageio_ffmpeg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script import RATE, SCENES, VOICE  # noqa: E402

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "work")
FF = imageio_ffmpeg.get_ffmpeg_exe()


def duration(path: Path) -> float:
    err = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def main() -> None:
    (WORK / "audio").mkdir(parents=True, exist_ok=True)
    out = {}
    for sid, _, text, _ in SCENES:
        path = WORK / "audio" / f"{sid}.mp3"
        await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))
        out[sid] = round(duration(path), 3)
        print(f"{sid:9s} {out[sid]:6.2f}s")
    (WORK / "durations.json").write_text(json.dumps(out, indent=2))
    print(f"total speech {sum(out.values()):.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
