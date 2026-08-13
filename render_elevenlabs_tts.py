#!/usr/bin/env python3
"""Generate ElevenLabs API TTS and render the video."""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate ElevenLabs API TTS and render the video.")
    parser.add_argument("slide_dir", help="Path to the slide directory")
    parser.add_argument("--voice", help="ElevenLabs voice_id")
    parser.add_argument("--model-id", help="ElevenLabs model id")
    parser.add_argument("--output-format", help="ElevenLabs output format")
    parser.add_argument("--speed", type=float, help="FFmpeg speed applied after ElevenLabs API audio generation")
    parser.add_argument("--size", default="1080x1920", help="Render size passed to auto_render.py (default: 1080x1920)")
    parser.add_argument("--config", help="Path to TTS config JSON")
    parser.add_argument("--force", action="store_true", help="Force regenerate audio")
    parser.add_argument("--no-subtitles", action="store_true", help="Disable script subtitle overlay")
    parser.add_argument("--outro", action="store_true", help="Append repo outro.mp4 to the final video")
    parser.add_argument("--outro-video", help="Custom outro video path used when --outro is enabled")
    parser.add_argument("--no-branding", action="store_true", help="Hide the starter Escbase corner branding")
    parser.add_argument("--brand-logo", help="Custom brand logo path for starter branding")
    parser.add_argument("--brand-name", default="", help="Custom brand text for starter branding")
    args = parser.parse_args()

    slide_dir = Path(args.slide_dir).resolve()
    if not slide_dir.exists():
        print(f"❌ Error: Slide directory {slide_dir} does not exist.")
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent

    print("\n=== 1. Generating ElevenLabs TTS ===")
    cmd_tts = [
        sys.executable,
        str(repo_root / "generate_tts.py"),
        str(slide_dir),
        "--engine",
        "elevenlabs",
    ]
    for flag, value in (
        ("--voice", args.voice),
        ("--model-id", args.model_id),
        ("--output-format", args.output_format),
        ("--voice-speed", f"{args.speed:g}" if args.speed else None),
        ("--config", args.config),
    ):
        if value:
            cmd_tts.extend([flag, value])
    if args.force:
        cmd_tts.append("--force")

    returncode = subprocess.run(cmd_tts).returncode
    if returncode:
        sys.exit(returncode)

    print("\n=== 2. Running auto_render.py ===")
    cmd_render = [
        sys.executable,
        str(repo_root / "auto_render.py"),
        str(slide_dir),
        "--size",
        args.size,
    ]
    if args.no_subtitles:
        cmd_render.append("--no-subtitles")
    if args.outro:
        cmd_render.append("--outro")
    if args.outro_video:
        cmd_render.extend(["--outro-video", args.outro_video])
    if args.no_branding:
        cmd_render.append("--no-branding")
    if args.brand_logo:
        cmd_render.extend(["--brand-logo", args.brand_logo])
    if args.brand_name:
        cmd_render.extend(["--brand-name", args.brand_name])
    returncode = subprocess.run(cmd_render).returncode
    if returncode:
        sys.exit(returncode)

    print("\n🎉 All done! Video rendered successfully.")


if __name__ == "__main__":
    main()
