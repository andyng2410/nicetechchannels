#!/usr/bin/env python3
"""Backfill cost-ledger từ lịch sử có sẵn (chạy trên HOST, nơi có ~/.codex/sessions).

Hai nguồn:
1. Rollout ~/.codex/sessions/**/rollout-*.jsonl của các lần `codex exec` chạy trong repo này
   -> event codex_run (dedupe theo session_id, chạy lại an toàn).
2. slide/<project>/output/elevenlabs_full_voiceover.meta.json chưa có event tts trong ledger
   -> synthesize 1 event tts từ độ dài text đã bill.

Usage: python3 cost_backfill.py [--dry-run] [--sessions-root PATH] [--slide-root PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import cost_tracking

REPO_ROOT = Path(__file__).resolve().parent

SLUG_RE = re.compile(r"Project slug bắt buộc:\s*([a-z0-9][a-z0-9-]{1,62})")
SLUG_REVISE_RE = re.compile(r"vòng SỬA deck slide/([a-z0-9][a-z0-9-]{1,62})/")
TIMESTAMP_RE = re.compile(r'"timestamp":"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})')
SESSION_FILE_RE = re.compile(
    r"rollout-.*-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$"
)


def detect_stage(raw_text: str) -> str | None:
    if "vòng SỬA deck slide/" in raw_text:
        return "revise"
    if "BƯỚC 1 của wizard" in raw_text or "DECK_DRAFTS: SUCCESS" in raw_text:
        return "drafts"
    if "Link Autopilot" in raw_text:
        return "build"
    return None


def detect_slug(raw_text: str) -> str | None:
    match = SLUG_RE.search(raw_text) or SLUG_REVISE_RE.search(raw_text)
    return match.group(1) if match else None


def rollout_duration_s(raw_text: str) -> float | None:
    stamps = TIMESTAMP_RE.findall(raw_text)
    if len(stamps) < 2:
        return None
    try:
        import datetime as dt

        first = dt.datetime.fromisoformat(stamps[0])
        last = dt.datetime.fromisoformat(stamps[-1])
        return max(0.0, (last - first).total_seconds())
    except ValueError:
        return None


def existing_session_ids(project_dir: Path) -> set[str]:
    return {
        str(event.get("session_id"))
        for event in cost_tracking.load_events(project_dir)
        if event.get("type") == "codex_run" and event.get("session_id")
    }


def has_tts_event(project_dir: Path, engine: str) -> bool:
    return any(
        event.get("type") == "tts" and str(event.get("engine") or "") == engine
        for event in cost_tracking.load_events(project_dir)
    )


def has_render_event(project_dir: Path) -> bool:
    return any(event.get("type") == "render" for event in cost_tracking.load_events(project_dir))


def backfill_codex(sessions_root: Path, slide_root: Path, dry_run: bool) -> int:
    added = 0
    for rollout in sorted(sessions_root.glob("*/*/*/rollout-*.jsonl")):
        session_match = SESSION_FILE_RE.search(rollout.name)
        session_id = session_match.group(1) if session_match else None
        parsed = cost_tracking.parse_rollout(rollout)
        if not parsed or parsed.get("originator") != "codex_exec":
            continue
        if str(parsed.get("cwd") or "") != str(REPO_ROOT):
            continue
        try:
            raw_text = rollout.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        stage = detect_stage(raw_text)
        slug = detect_slug(raw_text)
        if not stage or not slug:
            print(f"~ bỏ qua {rollout.name}: không nhận diện được stage/slug (stage={stage}, slug={slug})")
            continue
        project_dir = slide_root / slug
        if session_id and session_id in existing_session_ids(project_dir):
            continue
        tokens = parsed.get("tokens")
        model = str(parsed.get("model") or "unknown")
        event = {
            "type": "codex_run",
            "writer": "backfill",
            "job_id": None,
            "stage": stage,
            "mode": "runner",
            "model": model,
            "reasoning_effort": "",
            "tokens": tokens,
            "tokens_source": "rollout" if tokens else "missing",
            "session_id": session_id,
            "usd": cost_tracking.codex_usd(tokens, model, cost_tracking.load_pricing()),
            "duration_s": rollout_duration_s(raw_text),
            "returncode": None,
            "cancelled": False,
            "slide_count": cost_tracking.count_script_lines(project_dir),
            # notes revise không khôi phục được từ rollout -> phân bổ chia đều
            "notes": "",
            "usage_missing": tokens is None,
            "ts": rollout.stat().st_mtime,
        }
        total = (tokens or {}).get("total") or 0
        print(f"+ codex_run [{stage}] {slug}: {total:,} tokens (session {session_id}) <- {rollout.name}")
        if not dry_run:
            cost_tracking.append_event(project_dir, event)
        added += 1
    return added


def backfill_tts(slide_root: Path, dry_run: bool) -> int:
    added = 0
    sources = [
        ("elevenlabs", "elevenlabs_full_voiceover.meta.json", "voice_id"),
        ("edge", "edge_full_voiceover.meta.json", "voice"),
    ]
    for engine, meta_name, voice_key in sources:
        for meta_file in sorted(slide_root.glob(f"*/output/{meta_name}")):
            project_dir = meta_file.parents[1]
            if has_tts_event(project_dir, engine):
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            text = str(meta.get("text") or "")
            lines = meta.get("lines") if isinstance(meta.get("lines"), list) else []
            if not text:
                continue
            event = {
                "type": "tts",
                "writer": "backfill",
                "engine": engine,
                "mode": "full",
                "model_id": str(meta.get("model_id") or ""),
                "voice": str(meta.get(voice_key) or ""),
                "chars": len(text),
                "per_line_chars": [len(str(line)) for line in lines],
                "context_chars": 0,
                "cached": False,
                "cached_lines": [],
                "force": False,
                "usd": cost_tracking.tts_usd(len(text), engine, cost_tracking.load_pricing()),
                "slide_count": len(lines) or None,
                "ts": meta_file.stat().st_mtime,
            }
            print(f"+ tts [{engine}] {project_dir.name}: {len(text)} chars <- {meta_file.relative_to(slide_root)}")
            if not dry_run:
                cost_tracking.append_event(project_dir, event)
            added += 1
    return added


def backfill_render(slide_root: Path, dry_run: bool) -> int:
    """Project đã trót render trước khi có cost tracking: ước 1 event render từ kết quả để lại.

    Bằng chứng = final_video.mp4 + timing.json; wall_s lấy bằng tổng duration deck (sàn dưới —
    render tab-capture chạy real-time nên thời gian thật chỉ nhiều hơn). Đánh dấu estimated.
    """
    added = 0
    for timing_file in sorted(slide_root.glob("*/output/timing.json")):
        project_dir = timing_file.parents[1]
        final_video = project_dir / "output" / "final_video.mp4"
        if not final_video.is_file() or has_render_event(project_dir):
            continue
        try:
            timing_data = json.loads(timing_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(timing_data, list) or not timing_data:
            continue
        try:
            durations = [max(0.0, float(item.get("duration") or 0)) for item in timing_data]
        except (TypeError, AttributeError):
            continue
        deck_duration = round(sum(durations), 1)
        event = {
            "type": "render",
            "writer": "backfill",
            "status": "done",
            "estimated": True,
            "wall_s": deck_duration,
            "deck_duration_s": deck_duration,
            "per_slide_durations": durations,
            "size": None,
            "usd": cost_tracking.render_usd(deck_duration, cost_tracking.load_pricing()),
            "slide_count": len(durations),
            "ts": final_video.stat().st_mtime,
        }
        print(f"+ render (ước) {project_dir.name}: ≥{deck_duration:.0f}s <- final_video.mp4 + timing.json")
        if not dry_run:
            cost_tracking.append_event(project_dir, event)
        added += 1
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill cost-ledger từ rollout codex + meta ElevenLabs.")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in event dự kiến, không ghi")
    parser.add_argument("--sessions-root", default=str(Path.home() / ".codex" / "sessions"))
    parser.add_argument("--slide-root", default=str(REPO_ROOT / "slide"))
    args = parser.parse_args()

    sessions_root = Path(args.sessions_root)
    slide_root = Path(args.slide_root)
    if not slide_root.is_dir():
        print(f"Không thấy slide root: {slide_root}", file=sys.stderr)
        return 1

    codex_added = backfill_codex(sessions_root, slide_root, args.dry_run) if sessions_root.is_dir() else 0
    if not sessions_root.is_dir():
        print(f"~ bỏ qua codex backfill: không thấy {sessions_root}")
    tts_added = backfill_tts(slide_root, args.dry_run)
    render_added = backfill_render(slide_root, args.dry_run)
    mode = "DRY-RUN, chưa ghi" if args.dry_run else "đã ghi"
    print(f"Xong ({mode}): {codex_added} event codex_run, {tts_added} event tts, {render_added} event render (ước).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
