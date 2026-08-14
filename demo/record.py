#!/usr/bin/env python3
"""Render bug.html to demo.mp4 and demo.gif by stepping the timeline.

Playwright's own video recorder captures at viewport resolution, so scaling the
result down for a GIF softens every glyph. Screenshots taken at
device_scale_factor=2 are genuinely twice the size; downsampling those is
supersampling, and the text stays sharp.

Stepping also fixes the frame spacing. The recorder captures whatever the
compositor produced, which drops frames under load; setting `currentTime` on
each animation and shooting one frame per step gives an exactly even cadence
that is identical on every run.

    python3 record.py                 # 12 fps, 880 px wide
    python3 record.py --fps 24 --width 1100

ffmpeg comes from the imageio-ffmpeg wheel, so nothing outside this environment
has to be installed.
"""
import argparse, asyncio, pathlib, shutil, subprocess, sys

import imageio_ffmpeg
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
BEAT = 18.0                                   # matches --beat in bug.html
VIEW = {"width": 1270, "height": 660}


async def shoot(frames: pathlib.Path, fps: int) -> int:
    count = int(BEAT * fps)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await (await browser.new_context(
            viewport=VIEW, device_scale_factor=2)).new_page()
        await page.goto((HERE / "bug.html").as_uri())
        await page.wait_for_timeout(400)          # let fonts settle
        for i in range(count):
            ms = i * 1000 / fps
            # Pausing before seeking stops the compositor from advancing the
            # clock between the seek and the shutter.
            await page.evaluate(
                "t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })",
                ms)
            await page.screenshot(path=str(frames / f"f{i:05d}.png"))
        await browser.close()
    return count


def encode(frames: pathlib.Path, fps: int, width: int) -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    src = str(frames / "f%05d.png")
    scale = f"scale={width}:-2:flags=lanczos"

    subprocess.run([ff, "-y", "-framerate", str(fps), "-i", src,
                    "-vf", scale, "-c:v", "libx264", "-preset", "slow",
                    "-crf", "18", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(HERE / "demo.mp4")],
                   check=True, capture_output=True)

    palette = frames / "palette.png"
    subprocess.run([ff, "-y", "-framerate", str(fps), "-i", src, "-vf",
                    f"{scale},palettegen=stats_mode=diff", str(palette)],
                   check=True, capture_output=True)
    subprocess.run([ff, "-y", "-framerate", str(fps), "-i", src, "-i", str(palette),
                    "-lavfi", f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                    str(HERE / "demo.gif")], check=True, capture_output=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--width", type=int, default=880)
    args = ap.parse_args()

    frames = HERE / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    n = asyncio.run(shoot(frames, args.fps))
    encode(frames, args.fps, args.width)
    shutil.rmtree(frames)

    for name in ("demo.mp4", "demo.gif"):
        f = HERE / name
        print(f"{name:10s} {f.stat().st_size/1e6:5.2f} MB   ({n} frames @ {args.fps} fps, {args.width}px)")


main()
