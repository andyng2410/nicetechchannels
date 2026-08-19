from __future__ import annotations

import asyncio
import json
from pathlib import Path

from .common import generate_project_tts, record_tts_cost

DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
DEFAULT_RATE = "+0%"
MAX_RETRIES = 4
BASE_DELAY = 5.0
COOLDOWN = 5.0


async def generate_line_audio(text: str, audio_file: Path, subtitle_file: Path, voice: str, rate: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    submaker = edge_tts.SubMaker()

    with audio_file.open("wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    subtitle_file.write_text(submaker.get_srt(), encoding="utf-8")


async def generate_line_audio_with_retry(text: str, audio_file: Path, subtitle_file: Path, voice: str, rate: str) -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await generate_line_audio(text, audio_file, subtitle_file, voice, rate)
            return
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"  ⚠ Attempt {attempt} failed ({exc.__class__.__name__}), retrying in {wait:.0f}s...")
            await asyncio.sleep(wait)


async def generate_full_audio(text: str, audio_file: Path, voice: str, rate: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    with audio_file.open("wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


async def generate_full_audio_with_retry(text: str, audio_file: Path, voice: str, rate: str) -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await generate_full_audio(text, audio_file, voice, rate)
            return
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"  ⚠ Full Edge TTS attempt {attempt} failed ({exc.__class__.__name__}), retrying in {wait:.0f}s...")
            await asyncio.sleep(wait)


async def generate_edge_full_audio(
    slide_dir: Path,
    output_dir: Path,
    lines: list[str],
    *,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    full_text: str | None = None,
    force: bool = False,
) -> Path:
    text = full_text if full_text is not None else "\n".join(lines)
    if not text.strip():
        raise ValueError("No script text to send to Edge TTS.")

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_file = output_dir / "edge_full_voiceover.mp3"
    meta_file = output_dir / "edge_full_voiceover.meta.json"
    metadata = {
        "engine": "edge-tts",
        "mode": "full_voiceover",
        "text": text,
        "lines": lines,
        "voice": voice,
        "rate": rate,
    }
    cache_matches = False
    if meta_file.exists():
        try:
            cache_matches = json.loads(meta_file.read_text(encoding="utf-8")) == metadata
        except json.JSONDecodeError:
            cache_matches = False
    if not force and cache_matches and audio_file.exists() and audio_file.stat().st_size > 0:
        print(f"Full Edge TTS: {audio_file} (cached)")
        record_tts_cost(slide_dir, output_dir, {
            "engine": "edge",
            "mode": "full",
            "voice": voice,
            "chars": 0,
            "per_line_chars": [len(line) for line in lines],
            "context_chars": 0,
            "cached": True,
            "cached_lines": list(range(1, len(lines) + 1)),
            "force": force,
            "usd": 0.0,
            "slide_count": len(lines),
        })
        return audio_file

    if audio_file.exists():
        audio_file.unlink()
    print(f"Voice: Edge TTS {voice} ({rate}, full script in one request)")
    print(f"Sending full script to Edge TTS: {len(lines)} slides, {len(text)} chars")
    await generate_full_audio_with_retry(text, audio_file, voice, rate)
    meta_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Full Edge TTS saved: {audio_file}")
    record_tts_cost(slide_dir, output_dir, {
        "engine": "edge",
        "mode": "full",
        "voice": voice,
        "chars": len(text),
        "per_line_chars": [len(line) for line in lines],
        "context_chars": 0,
        "cached": False,
        "cached_lines": [],
        "force": force,
        "usd": 0.0,
        "slide_count": len(lines),
    })
    return audio_file


async def generate_edge_tts(
    slide_dir: Path,
    output_dir: Path,
    lines: list[str],
    *,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    force: bool = False,
) -> None:
    print(f"Voice: {voice} ({rate})")

    async def line_generator(index: int, text: str, audio_file: Path, subtitle_file: Path) -> None:
        await generate_line_audio_with_retry(text, audio_file, subtitle_file, voice, rate)

    generated_lines: list[int] = []
    cached_lines: list[int] = []

    def on_line_result(index: int, text: str, cached: bool) -> None:
        (cached_lines if cached else generated_lines).append(index)

    await generate_project_tts(
        slide_dir,
        output_dir,
        lines,
        line_generator,
        force=force,
        cooldown=COOLDOWN,
        on_line_result=on_line_result,
    )

    record_tts_cost(slide_dir, output_dir, {
        "engine": "edge",
        "mode": "per_slide",
        "voice": voice,
        "chars": sum(len(lines[i]) for i in generated_lines),
        "per_line_chars": [len(line) for line in lines],
        "context_chars": 0,
        "cached": not generated_lines,
        "cached_lines": [i + 1 for i in cached_lines],
        "force": force,
        "usd": 0.0,
        "slide_count": len(lines),
    })
