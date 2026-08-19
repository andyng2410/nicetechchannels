#!/usr/bin/env python3
"""Local web UI for previewing slide projects and starting render jobs."""

from __future__ import annotations

import argparse
import ast
import base64
import html
import json
import os
import re
import shutil
import shlex
import signal
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from social_upload import (
    build_upload_metadata,
    facebook_comment_source,
    facebook_upload_video,
    finish_youtube_oauth,
    set_facebook_active_page,
    set_youtube_active_channel,
    social_status,
    start_youtube_oauth,
    update_facebook_page_config,
    youtube_upload_video,
)
import cost_tracking
import social_upload.metadata as social_metadata
import branding

BRANDING_CLIENT_JSON = json.dumps(
    {"name": branding.BRANDING["name"], "handle": branding.BRANDING["handle"]},
    ensure_ascii=False,
)
from tts.elevenlabs import (
    elevenlabs_api_key,
    elevenlabs_config,
    elevenlabs_public_config,
    elevenlabs_voice_id,
    update_elevenlabs_api_key,
    update_elevenlabs_voice_id,
)


if sys.platform.startswith("win"):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_SLIDE_ROOT = REPO_ROOT / "slide"
SLIDE_ROOT = DEFAULT_SLIDE_ROOT
SOURCE_ROOT_IS_PROJECT = False
VENV_PYTHON = REPO_ROOT / ".venv" / ("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
RENDER_PYTHON = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8765
MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_LOG_CHARS = 240_000
AUDIO_UPLOAD_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm", ".flac"}
OUTRO_UPLOAD_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
BRAND_LOGO_UPLOAD_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".svg"}
MAX_LOGO_UPLOAD_BYTES = 20 * 1024 * 1024
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
ACTIVE_JOB_STATUSES = {"queued", "running", "cancelling"}
PRIVATE_JOB_FIELDS = {"process", "timer"}
SLIDE_AUDIO_SETTING_KEYS = {
    "transitionSounds": "slideTransitions",
    "revealSounds": "slideReveals",
}

RUNNING_IN_CONTAINER = Path("/.dockerenv").exists()
DECK_CONTAINER_NAME = "nicetechchannels"
DECK_RUNNER_HEARTBEAT_MAX_AGE = 15.0
DECK_AGENT_CONFIG_PATH = REPO_ROOT / "config" / "agent.json"
DECK_DEFAULT_AGENT_CONFIG = {
    "binary": "codex",
    "model": "",
    "reasoning_effort": "high",
    "sandbox": "workspace-write",
    "network_access": True,
    "extra_args": [],
    "timeout_minutes": 90,
}
DECK_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
DECK_STYLES = [
    {
        "value": "auto",
        "label": "Auto — agent tự chọn style hợp nguồn nhất",
        "prompt": "Style: đọc script-writing/STYLE_INDEX.md rồi tự chọn 1 style (hoặc 1 blend được phép: 4+1, 2+3, 5+3) hợp nguồn nhất; ghi rõ style đã chọn trong visual-plan.md.",
    },
    {
        "value": "style1",
        "label": "Style 1 — Sắc, đời, vào thẳng vấn đề",
        "prompt": "Style bắt buộc: style1.md — đọc script-writing/style1.md và viết script đúng màu giọng đó, không pha style khác.",
    },
    {
        "value": "style2",
        "label": "Style 2 — Mềm, thân thiện, dẫn người mới",
        "prompt": "Style bắt buộc: style2.md — đọc script-writing/style2.md và viết script đúng màu giọng đó, không pha style khác.",
    },
    {
        "value": "style3",
        "label": "Style 3 — Community/page, chia mục rõ",
        "prompt": "Style bắt buộc: style3.md — đọc script-writing/style3.md và viết script đúng màu giọng đó, không pha style khác.",
    },
    {
        "value": "style4",
        "label": "Style 4 — Phân tích sâu, điềm tĩnh",
        "prompt": "Style bắt buộc: style4.md — đọc script-writing/style4.md và viết script đúng màu giọng đó, không pha style khác.",
    },
    {
        "value": "style5",
        "label": "Style 5 — Năng lượng cao, kéo hành động",
        "prompt": "Style bắt buộc: style5.md — đọc script-writing/style5.md và viết script đúng màu giọng đó, không pha style khác.",
    },
    {
        "value": "blend-4-1",
        "label": "Blend 4+1 — Phân tích sâu, chốt sắc",
        "prompt": "Style bắt buộc: blend style4.md (chính) + style1.md (phụ) — blend được phép theo STYLE_INDEX.md, style4 giữ vai trò chủ đạo.",
    },
    {
        "value": "blend-2-3",
        "label": "Blend 2+3 — Mềm nhưng cấu trúc rõ",
        "prompt": "Style bắt buộc: blend style2.md (chính) + style3.md (phụ) — blend được phép theo STYLE_INDEX.md, style2 giữ vai trò chủ đạo.",
    },
    {
        "value": "blend-5-3",
        "label": "Blend 5+3 — Sôi động nhưng không loạn",
        "prompt": "Style bắt buộc: blend style5.md (chính) + style3.md (phụ) — blend được phép theo STYLE_INDEX.md, style5 giữ vai trò chủ đạo.",
    },
]
DECK_PROMPT_TEMPLATE = """Bạn đang chạy headless (codex exec) trong repo NiceTechChannels. Nhiệm vụ: dựng một deck slide HOÀN CHỈNH theo chế độ "Link Autopilot" trong WORKFLOW.md, dừng ở bước QA capture (KHÔNG render video).

Nguồn: {url}
Project slug bắt buộc: {slug} — toàn bộ output nằm trong slide/{slug}/
{style_instruction}
{notes_block}{tools_note}
Quy trình bắt buộc (theo đúng WORKFLOW.md, mục Link Autopilot):
1. Đọc kỹ AGENTS.md, WORKFLOW.md và các skill/rule được workflow gọi tới (skills/source-assets, skills/x-sources nếu là X/Twitter, skills/slide-visuals, script-writing/*) trước khi làm.
2. Thu source: tạo slide/{slug}/source/, lưu source gốc, facts, visual assets local và inventory source/source.md theo checklist source-assets.
3. Viết slide/{slug}/script-90s.txt theo đúng style chỉ định ở trên. Dòng CUỐI CÙNG của script-90s.txt phải là đúng nguyên văn câu outro cố định: "__OUTRO_LINE__" — dòng này KHÔNG tính vào nội dung, không viết thêm CTA đăng ký kênh nào khác trong các dòng nội dung. Tạo visual-plan.md với "Status: AUTO-APPROVED", ghi rõ style đã dùng.
4. Copy starter template/nicetechchannels-slide-starter, dựng đủ DOM/CSS/animation theo visual-first gate. Starter đã có sẵn SLIDE OUTRO cố định (marker data-outro, slide cuối): giữ nguyên DOM/CSS/copy/animation của nó, chỉ đổi data-slide cho đúng thứ tự cuối; KHÔNG redesign, KHÔNG tạo slide mới cho dòng outro. Slide outro được miễn visual-first gate, adjacent-slide variation và color-diversity (nó cố tình giống nhau ở mọi deck).__BRAND_NOTE__ Nếu starter có preview-assets/bgm/meta.mp3 thì copy kèm; nếu không có, ghi chú "BGM MISSING" rồi tiếp tục ngay, ĐỪNG mất thời gian đi tìm file này ở nơi khác.
5. Validate: {validate_cmd} — tự sửa đến khi PASS.
6. Capture QA: {capture_cmd} — bắt buộc dùng đúng --out này. Mở xem từng ảnh, tự sửa lỗi visual rồi capture lại đến khi đạt chuẩn bàn giao.

Cấm tuyệt đối:
- KHÔNG render video: không chạy render_elevenlabs.py, render_elevenlabs_tts.py, render_edgetts.py, auto_render.py.
- KHÔNG chạy web_server.py.
- KHÔNG gọi ElevenLabs hay bất kỳ TTS trả phí nào; không dùng --force.
- KHÔNG sửa file ngoài slide/{slug}/ (trừ file tạm hệ thống).

Progress marker: NGAY TRƯỚC khi bắt đầu mỗi giai đoạn, in ra một dòng riêng, đúng nguyên văn:
[PHASE] nguon
[PHASE] script
[PHASE] visual
[PHASE] validate
[PHASE] capture

Kết thúc: dòng CUỐI CÙNG của message cuối cùng phải là đúng MỘT trong hai dòng sau (không thêm gì phía sau):
DECK_BUILD: SUCCESS {slug}
DECK_BUILD: FAILED <lý do ngắn gọn một dòng>
Nếu nguồn không truy cập được hoặc thiếu dữ kiện cốt lõi, dừng sớm và báo DECK_BUILD: FAILED kèm lý do.
"""
DECK_DRAFTS_PROMPT_TEMPLATE = """Bạn đang chạy headless (codex exec) trong repo NiceTechChannels. Nhiệm vụ: BƯỚC 1 của wizard tạo deck — thu source và viết 5 bản nháp script để user chọn. KHÔNG dựng slide, KHÔNG copy starter, KHÔNG render.

Nguồn: {url}
Project slug bắt buộc: {slug} — chỉ được ghi vào slide/{slug}/source/
{notes_block}
Quy trình bắt buộc:
1. Đọc kỹ AGENTS.md, WORKFLOW.md, script-writing/START_HERE.md, SCRIPT_RULES.md, SCRIPT_PATTERNS.md, STYLE_INDEX.md và toàn bộ script-writing/style1.md..style5.md, cùng skills/source-assets/SKILL.md (và skills/x-sources/SKILL.md nếu nguồn là X/Twitter).
2. In dòng marker (nguyên văn, một dòng riêng): [PHASE] nguon — rồi thu source: tạo slide/{slug}/source/, lưu facts, visual assets local, links.txt và inventory source/source.md đúng checklist source-assets. Visual assets thu ở bước này sẽ được dùng khi build deck ở bước sau.
3. In dòng marker: [PHASE] drafts — rồi viết 5 bản script-90s HOÀN CHỈNH, mỗi bản đúng một style (style1..style5), theo đúng SCRIPT_RULES: 1 dòng = 1 slide (thường 6 dòng), slide 1 là hook một câu, không dùng dấu gạch dài, số câu mỗi dòng = số reveal. KHÔNG viết dòng outro hay CTA đăng ký kênh trong bất kỳ bản nháp nào — hệ thống tự thêm dòng outro cố định khi build.
4. Ghi file slide/{slug}/source/script-drafts.json đúng định dạng JSON sau (không markdown, không chú thích):
{{"drafts": [{{"style": "style1", "label": "tên ngắn của style", "hook": "dòng 1 của bản đó", "lines": ["dòng 1", "dòng 2", "..."]}}, ...đúng 5 phần tử, style1 đến style5...]}}

Cấm tuyệt đối: dựng DOM/CSS, copy starter, render video, chạy web_server.py, ghi file ngoài slide/{slug}/source/.

Kết thúc: dòng CUỐI CÙNG của message cuối cùng phải là đúng MỘT trong hai dòng sau:
DECK_DRAFTS: SUCCESS {slug}
DECK_DRAFTS: FAILED <lý do ngắn gọn một dòng>
Nếu nguồn không truy cập được hoặc thiếu dữ kiện cốt lõi, dừng sớm và báo DECK_DRAFTS: FAILED kèm lý do.
"""
DECK_REVISE_PROMPT_TEMPLATE = """Bạn đang chạy headless (codex exec) trong repo NiceTechChannels. Nhiệm vụ: vòng SỬA deck slide/{slug}/ theo yêu cầu user — deck đã build xong và có ảnh QA trong slide/{slug}/qa/.

Yêu cầu sửa từ user (làm đúng và đủ, không sửa lan man phần không được yêu cầu):
{notes}
{tools_note}
Quy trình bắt buộc:
1. Đọc AGENTS.md, WORKFLOW.md, skills/slide-visuals/SKILL.md. Xem ảnh QA hiện có trong slide/{slug}/qa/ để hiểu hiện trạng.
2. In dòng marker (nguyên văn, một dòng riêng): [PHASE] visual — rồi sửa deck theo yêu cầu. KHÔNG đổi script-90s.txt trừ khi yêu cầu nói rõ; nếu đổi thì phải đồng bộ slideScripts trong app.js và scriptLines trong preview-settings.json đúng WORKFLOW. KHÔNG sửa/xoá slide outro (marker data-outro) và dòng script cuối của nó, trừ khi yêu cầu user nêu đích danh outro.
3. In dòng marker: [PHASE] validate — rồi chạy: {validate_cmd} — tự sửa đến khi PASS.
4. In dòng marker: [PHASE] capture — rồi chạy: {capture_cmd} — capture lại toàn bộ, mở xem từng ảnh, tự sửa đến chuẩn bàn giao.

Cấm tuyệt đối: render video (render_elevenlabs*.py, render_edgetts.py, auto_render.py), web_server.py, ElevenLabs hay TTS trả phí, --force, ghi file ngoài slide/{slug}/.

Kết thúc: dòng CUỐI CÙNG của message cuối cùng phải là đúng MỘT trong hai dòng sau:
DECK_BUILD: SUCCESS {slug}
DECK_BUILD: FAILED <lý do ngắn gọn một dòng>
"""
DECK_PROMPT_TEMPLATE = DECK_PROMPT_TEMPLATE.replace("__OUTRO_LINE__", branding.OUTRO_SCRIPT_LINE)
_brand_note_parts = []
if (
    branding.BRANDING["name"],
    branding.BRANDING["handle"],
    branding.BRANDING["tagline"],
) != (
    branding.BRANDING_DEFAULTS["name"],
    branding.BRANDING_DEFAULTS["handle"],
    branding.BRANDING_DEFAULTS["tagline"],
):
    _brand_note_parts.append(
        ' Brand lấy từ config/branding.json: trong outro slide thay tên kênh thành "{name}" và tagline thành "{tagline}"; '
        'thay handle ở .brand-top-left/.brand-bottom-right thành "{handle}". Ngoài các text đó, giữ nguyên outro.'.format(
            name=branding.BRANDING["name"],
            tagline=branding.BRANDING["tagline"],
            handle=branding.BRANDING["handle"],
        )
    )
if branding.branding_logo_path():
    _brand_note_parts.append(
        ' Logo brand lấy từ config: copy file "{logo}" vào deck GHI ĐÈ lên logo-nicetechchannels.ico (giữ nguyên tên file, không sửa src trong DOM).'.format(
            logo=branding.branding_logo_path()
        )
    )
DECK_BRAND_NOTE = "".join(_brand_note_parts)
DECK_PROMPT_TEMPLATE = DECK_PROMPT_TEMPLATE.replace("__BRAND_NOTE__", DECK_BRAND_NOTE)


ANSI_ENABLED = os.environ.get("NO_COLOR") is None and (sys.stdout.isatty() or sys.stderr.isatty())
ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "blue": "\033[34m",
    "underline": "\033[4m",
} if ANSI_ENABLED else {key: "" for key in ["reset", "bold", "dim", "green", "cyan", "yellow", "red", "magenta", "blue", "underline"]}


def color_text(text: object, *styles: str) -> str:
    return "".join(ANSI.get(style, "") for style in styles) + str(text) + ANSI["reset"]


def json_dumps(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def configure_source_root(path: str | Path | None) -> None:
    global SLIDE_ROOT, SOURCE_ROOT_IS_PROJECT
    raw_path = Path(path).expanduser() if path else DEFAULT_SLIDE_ROOT
    source_root = raw_path.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"Source root not found: {source_root}")

    SLIDE_ROOT = source_root
    SOURCE_ROOT_IS_PROJECT = (SLIDE_ROOT / "index.html").is_file()
    social_metadata.SLIDE_ROOT = project_lookup_root()


def project_lookup_root() -> Path:
    return SLIDE_ROOT.parent if SOURCE_ROOT_IS_PROJECT else SLIDE_ROOT


def source_root_mode() -> str:
    return "single-project" if SOURCE_ROOT_IS_PROJECT else "collection"


def source_root_mode_for(path: Path) -> str:
    return "single-project" if (path / "index.html").is_file() else "collection"


def source_root_project_count(path: Path) -> int:
    if not path.is_dir():
        return 0
    if (path / "index.html").is_file():
        return 1
    return sum(1 for child in path.iterdir() if child.is_dir() and (child / "index.html").is_file())


def source_root_candidates() -> list[tuple[str, Path]]:
    raw_candidates = [
        ("Slide", DEFAULT_SLIDE_ROOT),
        ("Template", REPO_ROOT / "template"),
        ("Current", SLIDE_ROOT),
    ]
    cwd = Path.cwd().resolve()
    if cwd != REPO_ROOT and (cwd / "index.html").is_file():
        raw_candidates.append(("Current working folder", cwd))

    seen: set[Path] = set()
    candidates: list[tuple[str, Path]] = []
    for label, path in raw_candidates:
        resolved = path.expanduser().resolve()
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        candidates.append((label, resolved))
    return candidates


def source_root_option_payload() -> list[dict]:
    return [
        {
            "label": label,
            "path": str(path),
            "mode": source_root_mode_for(path),
            "projects": source_root_project_count(path),
            "active": path == SLIDE_ROOT,
        }
        for label, path in source_root_candidates()
    ]


def iter_project_dirs() -> list[Path]:
    if not SLIDE_ROOT.exists():
        return []
    if SOURCE_ROOT_IS_PROJECT:
        return [SLIDE_ROOT]
    return [path for path in SLIDE_ROOT.iterdir() if path.is_dir()]


def validate_project_name(project: str) -> str:
    project = unquote(str(project or "")).strip()
    if not project or project in {".", ".."} or "/" in project or "\\" in project or "\x00" in project:
        raise ValueError("Invalid project name.")
    return project


def project_url(project: str) -> str:
    return f"/slide/{quote(project)}/"


def source_root_response() -> dict:
    return {
        "source_root": str(SLIDE_ROOT),
        "source_mode": source_root_mode(),
        "options": source_root_option_payload(),
        "projects": list_projects(),
    }


def has_active_jobs() -> bool:
    with JOBS_LOCK:
        return any(
            job.get("status") in ACTIVE_JOB_STATUSES
            for job in JOBS.values()
        )


def choose_source_root_dialog() -> Path:
    if sys.platform == "darwin":
        script = 'POSIX path of (choose folder with prompt "Chọn source folder cho NiceTechChannels Web UI")'
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if proc.returncode != 0:
            message = (proc.stderr or proc.stdout or "").strip()
            if "User canceled" in message or proc.returncode == 1:
                raise RuntimeError("Đã huỷ chọn folder.")
            raise RuntimeError(message or "Không mở được Finder để chọn folder.")
        selected = proc.stdout.strip()
        if not selected:
            raise RuntimeError("Chưa chọn folder.")
        return Path(selected)

    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        raise RuntimeError("Máy này không hỗ trợ hộp chọn folder native.") from exc

    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askdirectory(title="Chọn source folder cho NiceTechChannels Web UI")
    finally:
        root.destroy()
    if not selected:
        raise RuntimeError("Đã huỷ chọn folder.")
    return Path(selected)


def project_created_at(project_dir: Path) -> float | None:
    """Ước thời điểm tạo project: mtime cũ nhất của file gốc (root + source/) — các file
    viết lúc build đầu và ít bị sửa lại. Kèm st_birthtime khi filesystem có (macOS)."""
    candidates: list[float] = []
    entries: list[Path] = []
    try:
        entries += [p for p in project_dir.iterdir() if p.is_file()]
    except OSError:
        return None
    source_dir = project_dir / "source"
    if source_dir.is_dir():
        try:
            entries += [p for p in source_dir.iterdir() if p.is_file()]
        except OSError:
            pass
    for path in entries:
        try:
            stat = path.stat()
        except OSError:
            continue
        candidates.append(stat.st_mtime)
        birthtime = getattr(stat, "st_birthtime", None)
        if birthtime:
            candidates.append(float(birthtime))
    return min(candidates) if candidates else None


def list_projects() -> list[dict]:
    if not SLIDE_ROOT.exists():
        return []

    projects = []
    project_dirs = list(iter_project_dirs())
    try:
        pricing = cost_tracking.load_pricing()
    except Exception:  # noqa: BLE001
        pricing = None
    for project_dir in project_dirs:
        if not project_dir.is_dir():
            continue
        if not (project_dir / "index.html").exists():
            continue
        try:
            cost = cost_tracking.project_cost_totals(project_dir, pricing) if pricing else None
        except Exception:  # noqa: BLE001
            cost = None
        try:
            updated_at = project_dir.stat().st_mtime
        except OSError:
            updated_at = 0
        created_at = project_created_at(project_dir) or updated_at
        script_path = project_dir / "script-90s.txt"
        output_dir = project_dir / "output"
        final_video = project_dir / "output" / "final_video.mp4"
        has_output = output_dir.is_dir() and any(output_dir.iterdir())
        output_url = final_video_url(project_dir.name)
        projects.append(
            {
                "name": project_dir.name,
                "url": project_url(project_dir.name),
                "source_path": str(project_dir),
                "has_script": script_path.exists(),
                "script_count": len(
                    [line for line in script_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                )
                if script_path.exists()
                else 0,
                "has_output": has_output,
                "output_url": output_url,
                "video_url": output_url if final_video.exists() else None,
                "cost": cost,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
    projects.sort(key=lambda item: (-(item["created_at"] or 0), item["name"].lower()))
    return projects


def require_slide_project(project: str) -> Path:
    project = validate_project_name(project)

    if SOURCE_ROOT_IS_PROJECT:
        if project != SLIDE_ROOT.name:
            raise FileNotFoundError(f"Slide project not found: {project}")
        project_dir = SLIDE_ROOT.resolve()
    else:
        project_dir = (SLIDE_ROOT / project).resolve()
    try:
        project_dir.relative_to(project_lookup_root().resolve())
    except ValueError as exc:
        raise ValueError("Invalid project path.") from exc

    if not project_dir.is_dir() or not (project_dir / "index.html").exists():
        raise FileNotFoundError(f"Slide project not found: {project}")
    return project_dir


def require_payload_project(payload: dict) -> str:
    project = str(payload.get("project") or "").strip()
    require_slide_project(project)
    return project


def coerce_speed(value: object) -> float:
    try:
        speed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Speed must be a number.") from exc
    if not 0.5 <= speed <= 2.0:
        raise ValueError("Speed must be between 0.5 and 2.0.")
    return speed


def coerce_render_size(value: object) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"", "720", "720x1280"}:
        return "720x1280"
    if raw in {"1080", "1080x1920"}:
        return "1080x1920"
    raise ValueError("Render size must be 1080x1920 or 720x1280.")


def clean_filename(name: str, fallback: str = "voiceover.mp3") -> str:
    cleaned = Path(name or fallback).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("._")
    return (cleaned or fallback)[:96]


def decode_audio_payload(audio: dict, project_dir: Path) -> Path:
    if not isinstance(audio, dict):
        raise ValueError("Missing ElevenLabs audio payload.")

    encoded = str(audio.get("data") or "")
    if "," in encoded:
        encoded = encoded.split(",", 1)[1]
    if not encoded:
        raise ValueError("Missing ElevenLabs audio data.")

    try:
        audio_bytes = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Audio payload is not valid base64.") from exc

    if not audio_bytes:
        raise ValueError("Uploaded audio is empty.")
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded audio is too large.")

    upload_dir = project_dir / "input_audio"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stamped_name = f"{time.strftime('%Y%m%d-%H%M%S')}_{clean_filename(str(audio.get('name') or 'voiceover.mp3'))}"
    audio_path = upload_dir / stamped_name
    audio_path.write_bytes(audio_bytes)
    return audio_path


def decode_render_asset_payload(
    payload: dict | None,
    project_dir: Path,
    *,
    kind: str,
    allowed_extensions: set[str],
    max_bytes: int,
) -> Path | None:
    if not payload:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid {kind} payload.")

    original_name = str(payload.get("name") or "")
    ext = Path(original_name).suffix.lower()
    if ext not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"{kind} file must be one of: {allowed}.")

    encoded = str(payload.get("data") or "")
    if "," in encoded:
        encoded = encoded.split(",", 1)[1]
    if not encoded:
        raise ValueError(f"Missing {kind} file data.")

    try:
        file_bytes = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError(f"{kind} payload is not valid base64.") from exc

    if not file_bytes:
        raise ValueError(f"{kind} file is empty.")
    if len(file_bytes) > max_bytes:
        raise ValueError(f"{kind} file is too large.")

    upload_dir = project_dir / "assets" / "render-options"
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_path = upload_dir / f"{kind}{ext}"
    output_path.write_bytes(file_bytes)
    return output_path


def clean_brand_name(value: object) -> str:
    name = re.sub(r"\s+", " ", str(value or "").strip())
    if len(name) > 64:
        raise ValueError("Brand name must be 64 characters or shorter.")
    return name


def append_render_asset_options(cmd: list[str], payload: dict, project_dir: Path) -> None:
    # Checkbox Outro theo cùng logic với Logo/Brand: bỏ tick = không outro,
    # tick = outro slide mặc định của deck, tick + upload = video upload THAY THẾ.
    # outro.mp4 mẫu ở repo root không còn được dashboard nối mặc định.
    has_outro_slide = social_metadata.project_has_outro_slide(project_dir)
    if bool(payload.get("outro", True)):
        outro_video = decode_render_asset_payload(
            payload.get("outroFile") or payload.get("outro_file"),
            project_dir,
            kind="outro",
            allowed_extensions=OUTRO_UPLOAD_EXTENSIONS,
            max_bytes=MAX_UPLOAD_BYTES,
        )
        if outro_video:
            cmd.extend(["--outro", "--outro-video", str(outro_video)])
            if has_outro_slide:
                cmd.append("--skip-outro-slide")
        elif not has_outro_slide:
            print(
                f"[render] {project_dir.name}: deck chưa có outro slide; outro mẫu đã bỏ, video sẽ không có outro",
                flush=True,
            )
    elif has_outro_slide:
        cmd.append("--skip-outro-slide")

    if not bool(payload.get("branding", True)):
        cmd.append("--no-branding")
        return

    brand_logo = decode_render_asset_payload(
        payload.get("brandLogo") or payload.get("brand_logo"),
        project_dir,
        kind="brand-logo",
        allowed_extensions=BRAND_LOGO_UPLOAD_EXTENSIONS,
        max_bytes=MAX_LOGO_UPLOAD_BYTES,
    )
    if brand_logo:
        cmd.extend(["--brand-logo", str(brand_logo)])
    else:
        config_logo = branding.branding_logo_path()
        if config_logo:
            # Không upload logo riêng: overlay render dùng logo từ config/branding.json.
            cmd.extend(["--brand-logo", str(config_logo)])

    brand_name = clean_brand_name(payload.get("brandName") or payload.get("brand_name"))
    if brand_name:
        cmd.extend(["--brand-name", brand_name])
    elif branding.BRANDING["handle"] != branding.BRANDING_DEFAULTS["handle"]:
        # Deck cũ còn handle mặc định trong DOM: overlay render đè handle theo config.
        cmd.extend(["--brand-name", branding.BRANDING["handle"]])


def quote_relative_url(path: str) -> str:
    return "/".join(quote(part) for part in path.split("/"))


def upload_preview_bgm(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    project_dir = require_slide_project(project)
    audio = payload.get("audio")
    if not isinstance(audio, dict):
        raise ValueError("Missing BGM audio payload.")

    encoded = str(audio.get("data") or "")
    if "," in encoded:
        encoded = encoded.split(",", 1)[1]
    if not encoded:
        raise ValueError("Missing BGM audio data.")

    try:
        audio_bytes = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("BGM payload is not valid base64.") from exc

    if not audio_bytes:
        raise ValueError("Uploaded BGM is empty.")
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded BGM is too large.")

    filename = clean_filename(str(audio.get("name") or "background.mp3"), "background.mp3")
    suffix = Path(filename).suffix.lower()
    if suffix not in AUDIO_UPLOAD_EXTENSIONS:
        raise ValueError("BGM file must be an audio file.")

    upload_dir = project_dir / "preview-assets" / "bgm"
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{time.strftime('%Y%m%d-%H%M%S')}_{filename}"
    audio_path = upload_dir / saved_name
    audio_path.write_bytes(audio_bytes)
    rel_path = audio_path.relative_to(project_dir).as_posix()
    return {
        "project": project_dir.name,
        "audio": {
            "name": filename,
            "path": rel_path,
            "url": project_url(project_dir.name) + quote_relative_url(rel_path),
            "size": len(audio_bytes),
        },
    }


def preview_settings_path(project: str) -> Path:
    return require_slide_project(project) / "preview-settings.json"


def read_preview_settings(project: str) -> dict:
    path = preview_settings_path(project)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"preview-settings.json is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("preview-settings.json must contain a JSON object.")
    return data


def write_preview_settings(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("Missing preview settings.")
    path = preview_settings_path(project)
    settings = sync_settings_script_lines(path.parent, settings)
    encoded = json.dumps(settings, ensure_ascii=False, indent=2).encode("utf-8")
    if len(encoded) > 200_000:
        raise ValueError("Preview settings are too large.")
    path.write_bytes(encoded + b"\n")
    app_js_synced = sync_app_js_preview_settings(path.parent, settings)
    return {"project": project, "settings": settings, "app_js_synced": app_js_synced}


def clean_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [str(item).strip() for item in value]
    return [item for item in cleaned if item]


def js_literal(value: object, base_indent: str = "") -> str:
    literal = json.dumps(value, ensure_ascii=False, indent=2)
    if "\n" not in literal or not base_indent:
        return literal
    lines = literal.splitlines()
    return lines[0] + "\n" + "\n".join(f"{base_indent}{line}" for line in lines[1:])


def js_literal_span(source: str, start: int) -> tuple[int, int]:
    idx = start
    while idx < len(source) and source[idx].isspace():
        idx += 1
    if idx >= len(source) or source[idx] not in "[{(":
        raise ValueError("Expected JS literal.")
    open_to_close = {"[": "]", "{": "}", "(": ")"}
    literal_start = idx
    stack: list[str] = []
    quote = ""
    escaped = False
    line_comment = False
    block_comment = False
    while idx < len(source):
        char = source[idx]
        next_char = source[idx + 1] if idx + 1 < len(source) else ""
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            idx += 1
            continue
        if line_comment:
            if char == "\n":
                line_comment = False
            idx += 1
            continue
        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                idx += 2
                continue
            idx += 1
            continue
        if char == "/" and next_char == "/":
            line_comment = True
            idx += 2
            continue
        if char == "/" and next_char == "*":
            block_comment = True
            idx += 2
            continue
        if char in {"'", '"', "`"}:
            quote = char
            idx += 1
            continue
        if char in open_to_close:
            stack.append(open_to_close[char])
        elif char in {"]", "}", ")"}:
            if not stack or char != stack[-1]:
                raise ValueError("Malformed JS literal.")
            stack.pop()
            if not stack:
                return literal_start, idx + 1
        idx += 1
    raise ValueError("Unterminated JS literal.")


def js_const_literal_span(source: str, const_name: str) -> tuple[int, int]:
    match = re.search(rf"\bconst\s+{re.escape(const_name)}\s*=\s*", source)
    if not match:
        raise ValueError(f"Missing const {const_name}.")
    return js_literal_span(source, match.end())


def read_js_const_literal(project_dir: Path, const_name: str) -> object | None:
    path = project_dir / "app.js"
    if not path.exists():
        return None
    source = path.read_text(encoding="utf-8")
    try:
        start, end = js_const_literal_span(source, const_name)
        return ast.literal_eval(source[start:end])
    except Exception:
        return None


def replace_js_const_literal(source: str, const_name: str, value: object) -> str:
    start, end = js_const_literal_span(source, const_name)
    line_start = source.rfind("\n", 0, start) + 1
    base_indent = re.match(r"\s*", source[line_start:start]).group(0)
    return source[:start] + js_literal(value, base_indent) + source[end:]


def replace_default_preview_script_lines(source: str, lines: list[str]) -> str:
    object_start, object_end = js_const_literal_span(source, "defaultPreviewSettings")
    object_source = source[object_start:object_end]
    match = re.search(r'(?m)^(\s*)(["\']?scriptLines["\']?\s*:\s*)', object_source)
    if not match:
        raise ValueError("Missing defaultPreviewSettings.slides.scriptLines.")
    value_start = object_start + match.end()
    value_end = js_literal_span(source, value_start)[1]
    return source[:value_start] + js_literal(lines, match.group(1)) + source[value_end:]


def sync_app_js_script_lines(project_dir: Path, lines: list[str]) -> bool:
    path = project_dir / "app.js"
    if not path.exists():
        return False
    source = path.read_text(encoding="utf-8")
    updated = replace_js_const_literal(source, "slideScripts", lines)
    updated = replace_default_preview_script_lines(updated, lines)
    if updated != source:
        path.write_text(updated, encoding="utf-8")
    return updated != source


def sync_app_js_preview_settings(project_dir: Path, settings: dict) -> bool:
    path = project_dir / "app.js"
    if not path.exists():
        return False
    source = path.read_text(encoding="utf-8")
    updated = replace_js_const_literal(source, "defaultPreviewSettings", settings)
    script_lines = settings.get("slides", {}).get("scriptLines", [])
    if isinstance(script_lines, list) and script_lines and all(isinstance(line, str) for line in script_lines):
        updated = replace_js_const_literal(updated, "slideScripts", script_lines)
    slides = settings.get("slides", {})
    if isinstance(slides, dict):
        for setting_key, const_name in SLIDE_AUDIO_SETTING_KEYS.items():
            values = clean_string_list(slides.get(setting_key))
            if values:
                updated = replace_js_const_literal(updated, const_name, values)
    if updated != source:
        path.write_text(updated, encoding="utf-8")
    return updated != source


def read_script_lines_from_path(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sync_settings_script_lines(project_dir: Path, settings: dict) -> dict:
    script_lines = read_script_lines_from_path(project_dir / "script-90s.txt")
    synced = json.loads(json.dumps(settings, ensure_ascii=False))
    slides = synced.get("slides")
    if not isinstance(slides, dict):
        slides = {}
    if script_lines:
        slides["scriptLines"] = script_lines
    existing_slides: dict = {}
    settings_path = project_dir / "preview-settings.json"
    if settings_path.exists():
        try:
            existing_settings = json.loads(settings_path.read_text(encoding="utf-8"))
            if isinstance(existing_settings, dict) and isinstance(existing_settings.get("slides"), dict):
                existing_slides = existing_settings["slides"]
        except json.JSONDecodeError:
            existing_slides = {}
    for setting_key, const_name in SLIDE_AUDIO_SETTING_KEYS.items():
        values = clean_string_list(slides.get(setting_key))
        if not values:
            values = clean_string_list(existing_slides.get(setting_key))
        if not values:
            values = clean_string_list(read_js_const_literal(project_dir, const_name))
        if values:
            slides[setting_key] = values
    synced["slides"] = slides
    return synced


def sync_preview_settings_script_lines(project_dir: Path, lines: list[str]) -> dict:
    path = project_dir / "preview-settings.json"
    settings: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"preview-settings.json is invalid: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("preview-settings.json must contain a JSON object.")
        settings = data
    slides = settings.get("slides")
    if not isinstance(slides, dict):
        slides = {}
    slides["scriptLines"] = lines
    for setting_key, const_name in SLIDE_AUDIO_SETTING_KEYS.items():
        values = clean_string_list(slides.get(setting_key))
        if not values:
            values = clean_string_list(read_js_const_literal(project_dir, const_name))
        if values:
            slides[setting_key] = values
    settings["slides"] = slides
    encoded = json.dumps(settings, ensure_ascii=False, indent=2).encode("utf-8")
    if len(encoded) > 200_000:
        raise ValueError("Preview settings are too large.")
    path.write_bytes(encoded + b"\n")
    return settings


def slide_script_path(project: str) -> Path:
    return require_slide_project(project) / "script-90s.txt"


def read_slide_script(project: str) -> dict:
    path = slide_script_path(project)
    return {"project": project, "lines": read_script_lines_from_path(path)}


def write_slide_script(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    path = slide_script_path(project)
    lines = payload.get("lines")
    allow_count_change = bool(payload.get("allowCountChange") or payload.get("allow_count_change"))
    if not isinstance(lines, list):
        raise ValueError("Missing script lines.")
    cleaned = [str(line).strip() for line in lines]
    if not cleaned or any(not line for line in cleaned):
        raise ValueError("Script lines cannot be empty.")
    existing_count = len(read_slide_script(project)["lines"])
    if existing_count and len(cleaned) != existing_count and not allow_count_change:
        raise ValueError(f"Expected {existing_count} script lines.")
    encoded = ("\n".join(cleaned) + "\n").encode("utf-8")
    if len(encoded) > 100_000:
        raise ValueError("Script is too large.")
    project_dir = path.parent
    existing_metadata = social_metadata.read_project_upload_metadata(project_dir)
    upload_metadata = social_metadata.generated_upload_metadata(project_dir, cleaned, existing_metadata)
    path.write_bytes(encoded)
    social_metadata.write_project_upload_metadata(project_dir, upload_metadata)
    sync_preview_settings_script_lines(project_dir, cleaned)
    app_js_synced = sync_app_js_script_lines(project_dir, cleaned)
    return {"project": project, "lines": cleaned, "upload_metadata": upload_metadata, "app_js_synced": app_js_synced}


def append_log(job_id: str, text: str) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job["logs"] = (job.get("logs", "") + text)[-MAX_LOG_CHARS:]
        job["updated_at"] = time.time()


def set_job_state(job_id: str, **updates: object) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updated_at"] = time.time()


def public_job(job: dict) -> dict:
    return {key: value for key, value in job.items() if key not in PRIVATE_JOB_FIELDS}


def job_cancel_requested(job_id: str) -> bool:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return bool(job and job.get("cancel_requested"))


def job_field(job_id: str, key: str) -> object:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return job.get(key) if job else None


def failure_summary(logs: str, returncode: int) -> str:
    lines = [line.strip() for line in str(logs or "").splitlines() if line.strip()]
    skip_patterns = (
        r"^\$ ",
        r"^Traceback ",
        r"^File ",
        r"^\^+$",
        r"^Render failed with exit code ",
        r"returned non-zero exit status",
    )
    candidates = []
    for line in lines:
        if any(re.search(pattern, line) for pattern in skip_patterns):
            continue
        if re.search(r"(Missing ElevenLabs|ElevenLabs API failed|ElevenLabs TTS failed|Missing ElevenLabs SDK|Invalid ElevenLabs|ValueError:|RuntimeError:|ModuleNotFoundError:|FileNotFoundError:|❌)", line):
            candidates.append(line)
    if candidates:
        summary = candidates[-1]
        summary = re.sub(r"^❌\s*", "", summary)
        return re.sub(r"^(ValueError|RuntimeError|ModuleNotFoundError|FileNotFoundError):\s*", "", summary)
    for line in reversed(lines):
        if not any(re.search(pattern, line) for pattern in skip_patterns):
            return line
    return f"Render failed with exit code {returncode}."


def final_video_url(project: str) -> str:
    return f"/slide/{quote(project)}/output/final_video.mp4"


def run_job(job_id: str, cmd: list[str], project: str, stdin_data: str | None = None) -> None:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    pretty_cmd = " ".join(shlex.quote(part) for part in cmd)
    job_type = job_field(job_id, "job_type") or "render"

    set_job_state(job_id, status="running", command=pretty_cmd, started_at=time.time())
    append_log(job_id, f"$ {pretty_cmd}\n\n")
    if stdin_data is not None:
        append_log(job_id, f"(prompt {len(stdin_data)} ký tự gửi qua stdin)\n\n")
    if job_cancel_requested(job_id):
        append_log(job_id, "Render stopped before process start.\n")
        set_job_state(job_id, status="cancelled", returncode=None, finished_at=time.time())
        finish_deck_job_cleanup(job_id)
        return

    try:
        popen_kwargs = {}
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if creationflags:
                popen_kwargs["creationflags"] = creationflags
        else:
            popen_kwargs["start_new_session"] = True
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdin=subprocess.PIPE if stdin_data is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            **popen_kwargs,
        )
        set_job_state(job_id, process=proc, pid=proc.pid)
    except Exception as exc:
        append_log(job_id, f"Failed to start render: {exc}\n")
        set_job_state(job_id, status="failed", returncode=-1, finished_at=time.time())
        finish_deck_job_cleanup(job_id)
        return

    if job_type == "deck":
        write_deck_lock(job_id, proc.pid, project)
    if stdin_data is not None and proc.stdin is not None:
        try:
            proc.stdin.write(stdin_data)
            proc.stdin.close()
        except Exception as exc:
            append_log(job_id, f"Không gửi được prompt qua stdin: {exc}\n")

    assert proc.stdout is not None
    # Bắt session id ngay khi stream: log bị cắt giữ tail 240k nên header có thể mất sau này.
    session_scan_remaining = 80 if job_type == "deck" else 0
    for line in proc.stdout:
        append_log(job_id, line)
        if session_scan_remaining > 0:
            session_scan_remaining -= 1
            session_id = cost_tracking.parse_session_id(line)
            if session_id:
                set_job_state(job_id, codex_session_id=session_id)
                session_scan_remaining = 0

    returncode = proc.wait()
    set_job_state(job_id, process=None, pid=None)
    if job_type == "deck":
        record_deck_run_cost(job_id, project, returncode)
    if job_cancel_requested(job_id):
        finish_deck_job_cleanup(job_id)
        if job_field(job_id, "timeout_hit"):
            set_job_state(job_id, returncode=returncode)
            return
        append_log(job_id, "\nRender stopped by user.\n")
        set_job_state(job_id, status="cancelled", returncode=returncode, finished_at=time.time())
        return
    if job_type == "deck":
        finish_deck_job_cleanup(job_id)
        finalize_deck_stage(job_id, project, returncode)
        return
    try:
        project_dir = require_slide_project(project)
    except Exception:
        project_dir = project_lookup_root() / project
    video_path = project_dir / "output" / "final_video.mp4"

    if returncode == 0 and video_path.exists():
        append_log(job_id, f"\nDone: {video_path}\n")
        set_job_state(
            job_id,
            status="done",
            returncode=returncode,
            finished_at=time.time(),
            video_url=final_video_url(project),
        )
    elif returncode == 0:
        append_log(job_id, "\nRender finished, but final_video.mp4 was not found.\n")
        set_job_state(job_id, status="failed", returncode=returncode, finished_at=time.time())
    else:
        with JOBS_LOCK:
            logs = str((JOBS.get(job_id) or {}).get("logs") or "")
        summary = failure_summary(logs, returncode)
        append_log(job_id, f"\nRender failed: {summary}\n")
        set_job_state(job_id, status="failed", returncode=returncode, finished_at=time.time(), error=summary)


def build_render_command(payload: dict) -> tuple[list[str], str]:
    project = str(payload.get("project") or "").strip()
    project_dir = require_slide_project(project)
    speed = coerce_speed(payload.get("speed", 1.1))
    render_size = coerce_render_size(payload.get("size", "720x1280"))
    engine = str(payload.get("engine") or "").strip().lower()

    if engine in {"elevenlabs", "elevenlab"}:
        mode = str(payload.get("mode") or "tts").strip().lower()
        if mode == "upload":
            audio_path = decode_audio_payload(payload.get("audio", {}), project_dir)
            cmd = [
                str(RENDER_PYTHON),
                "-u",
                str(REPO_ROOT / "render_elevenlabs.py"),
                str(project_dir),
                str(audio_path),
                "--speed",
                f"{speed:g}",
                "--size",
                render_size,
            ]
            append_render_asset_options(cmd, payload, project_dir)
            return cmd, "elevenlabs-upload"
        if mode not in {"tts", "api", "elevenlabs-tts"}:
            raise ValueError("ElevenLabs mode must be tts or upload.")
        voice = str(payload.get("voice") or "").strip()
        config = elevenlabs_config()
        elevenlabs_api_key(None, config)
        elevenlabs_voice_id(voice or None, config)
        try:
            import elevenlabs.client
        except ImportError as exc:
            raise ValueError("Missing ElevenLabs SDK. Run ./install.sh or pip install -r requirements.txt.") from exc
        cmd = [
            str(RENDER_PYTHON),
            "-u",
            str(REPO_ROOT / "render_elevenlabs_tts.py"),
            str(project_dir),
            "--speed",
            f"{speed:g}",
            "--size",
            render_size,
        ]
        if voice:
            if not re.fullmatch(r"[A-Za-z0-9._-]+", voice):
                raise ValueError("Invalid ElevenLabs voice id.")
            cmd.extend(["--voice", voice])
        model_id = str(payload.get("modelId") or "").strip()
        if model_id:
            if not re.fullmatch(r"[A-Za-z0-9._-]+", model_id):
                raise ValueError("Invalid ElevenLabs model id.")
            cmd.extend(["--model-id", model_id])
        output_format = str(payload.get("outputFormat") or "").strip()
        if output_format:
            if not re.fullmatch(r"[A-Za-z0-9._-]+", output_format):
                raise ValueError("Invalid ElevenLabs output format.")
            cmd.extend(["--output-format", output_format])
        if bool(payload.get("force")):
            cmd.append("--force")
        append_render_asset_options(cmd, payload, project_dir)
        return cmd, "elevenlabs"

    if engine in {"edgetts", "edtts", "edge_tts", "edge-tts"}:
        voice = str(payload.get("voice") or "vi-VN-HoaiMyNeural").strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]+", voice):
            raise ValueError("Invalid Edge TTS voice name.")
        per_slide = bool(payload.get("edgePerSlide") or payload.get("edge_per_slide") or payload.get("perSlide"))
        cmd = [
            str(RENDER_PYTHON),
            "-u",
            str(REPO_ROOT / "render_edgetts.py"),
            str(project_dir),
            "--speed",
            f"{speed:g}",
            "--voice",
            voice,
            "--size",
            render_size,
            "--edge-mode",
            "per-slide" if per_slide else "full",
        ]
        if bool(payload.get("force")):
            cmd.append("--force")
        append_render_asset_options(cmd, payload, project_dir)
        return cmd, "edgetts"

    raise ValueError("Engine must be elevenlabs or edgetts.")


def has_running_job(project: str) -> bool:
    with JOBS_LOCK:
        return any(
            job.get("project") == project and job.get("status") in ACTIVE_JOB_STATUSES
            for job in JOBS.values()
        )


def create_job(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    require_slide_project(project)

    if has_running_job(project):
        raise RuntimeError(f"Project '{project}' already has a running render job.")

    cmd, engine = build_render_command(payload)
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    job = {
        "id": job_id,
        "project": project,
        "job_type": "render",
        "engine": engine,
        "status": "queued",
        "logs": "",
        "created_at": now,
        "updated_at": now,
        "video_url": None,
    }

    with JOBS_LOCK:
        JOBS[job_id] = job

    thread = threading.Thread(target=run_job, args=(job_id, cmd, project), daemon=True)
    thread.start()
    return public_job(job)


def get_job(job_id: str) -> dict | None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return public_job(job) if job else None


def terminate_process(proc: subprocess.Popen) -> bool:
    if proc.poll() is not None:
        return True
    try:
        if os.name == "nt":
            proc.terminate()
        else:
            os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        proc.terminate()
    try:
        proc.wait(timeout=5)
        return True
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "nt":
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        proc.kill()
    try:
        proc.wait(timeout=5)
        return True
    except subprocess.TimeoutExpired:
        return False


def cancel_job(job_id: str) -> dict | None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return None
        status = str(job.get("status") or "")
        if status not in ACTIVE_JOB_STATUSES:
            return public_job(job)
        job["cancel_requested"] = True
        job["status"] = "cancelling"
        job["updated_at"] = time.time()
        proc = job.get("process")

    append_log(job_id, "\nStop requested by user.\n")
    if isinstance(proc, subprocess.Popen):
        if terminate_process(proc):
            set_job_state(job_id, status="cancelled", returncode=proc.returncode, process=None, pid=None, finished_at=time.time())
        finish_deck_job_cleanup(job_id)
        return get_job(job_id)
    with JOBS_LOCK:
        job_entry = JOBS.get(job_id)
        is_runner_job = bool(job_entry and job_entry.get("runner"))
    if is_runner_job:
        # monitor thread sẽ gửi file cancel cho host runner và tự chốt trạng thái
        return get_job(job_id)
    set_job_state(job_id, status="cancelled", returncode=None, finished_at=time.time())
    finish_deck_job_cleanup(job_id)
    return get_job(job_id)


# ---------------------------------------------------------------------------
# Deck builder (Codex CLI headless): dán URL -> job "deck" chạy Link Autopilot
# ---------------------------------------------------------------------------


def load_agent_config() -> dict:
    config = dict(DECK_DEFAULT_AGENT_CONFIG)
    try:
        raw = json.loads(DECK_AGENT_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return config
    section = raw.get("codex") if isinstance(raw, dict) else None
    if isinstance(section, dict):
        for key in config:
            if key in section and section[key] is not None:
                config[key] = section[key]
    return config


def is_loopback_client(handler) -> bool:
    # Trong container, client_address là IP proxy của Docker chứ không phải IP thật;
    # cổng đã bind 127.0.0.1 ở compose nên quyền truy cập do host quyết định.
    if RUNNING_IN_CONTAINER:
        return True
    host = str(handler.client_address[0] if handler.client_address else "")
    return host in {"127.0.0.1", "::1", "::ffff:127.0.0.1"} or host.startswith("127.")


def codex_binary_path(config: dict | None = None) -> str | None:
    config = config or load_agent_config()
    return shutil.which(str(config.get("binary") or "codex"))


def deck_runner_root() -> Path:
    return project_lookup_root() / ".deck-runner"


def deck_runner_jobs_root() -> Path:
    return deck_runner_root() / "jobs"


def deck_runner_heartbeat_fresh() -> bool:
    path = deck_runner_root() / "heartbeat.json"
    try:
        return (time.time() - path.stat().st_mtime) < DECK_RUNNER_HEARTBEAT_MAX_AGE
    except OSError:
        return False


def deck_runner_job_paths(job_id: str) -> dict[str, Path]:
    root = deck_runner_jobs_root()
    return {
        "request": root / f"{job_id}.request.json",
        "status": root / f"{job_id}.status.json",
        "log": root / f"{job_id}.log",
        "cancel": root / f"{job_id}.cancel",
    }


def deck_runner_read_status(job_id: str) -> dict | None:
    try:
        data = json.loads(deck_runner_job_paths(job_id)["status"].read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def deck_runner_running_job_ids() -> list[str]:
    jobs_root = deck_runner_jobs_root()
    if not jobs_root.is_dir():
        return []
    running = []
    for status_path in jobs_root.glob("*.status.json"):
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("status") == "running":
            if (time.time() - status_path.stat().st_mtime) < 2 * 3600:
                running.append(status_path.name.rsplit(".status.json", 1)[0])
    return running


def deck_feature_state(config: dict | None = None) -> tuple[bool, str | None, str | None]:
    """Trả (available, reason, mode). mode: 'local' (spawn codex tại chỗ) hoặc 'runner' (host runner qua file queue)."""
    config = config or load_agent_config()
    if SOURCE_ROOT_IS_PROJECT or (not RUNNING_IN_CONTAINER and SLIDE_ROOT.resolve() != DEFAULT_SLIDE_ROOT.resolve()):
        return False, "custom-source-root", None
    if codex_binary_path(config):
        return True, None, "local"
    if deck_runner_heartbeat_fresh():
        return True, None, "runner"
    if RUNNING_IN_CONTAINER:
        return False, "runner-missing", None
    return False, "codex-missing", None


def deck_unavailable_message(reason: str | None) -> str:
    if reason == "codex-missing":
        return (
            "Không tìm thấy Codex CLI. Cài trên máy host: npm i -g @openai/codex rồi codex login, "
            "hoặc chạy python3 deck_host_runner.py trên host nếu server đang ở container."
        )
    if reason == "runner-missing":
        return (
            "Chưa thấy host runner. Trên máy host, mở terminal trong thư mục repo và chạy: "
            "python3 deck_host_runner.py — rồi tải lại trang này."
        )
    if reason == "custom-source-root":
        return "Tạo deck tự động chỉ hỗ trợ source root slide/ mặc định của repo. Đổi Source root về mặc định rồi thử lại."
    return "Deck builder hiện không khả dụng."


def derive_deck_slug(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    segments = [segment for segment in parsed.path.split("/") if segment]

    def sanitize(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    if host.endswith("github.com") and len(segments) >= 2:
        repo_name = re.sub(r"\.git$", "", segments[1])
        slug = sanitize(f"{segments[0]}-{repo_name}")
    elif host in {"x.com", "twitter.com", "www.x.com", "www.twitter.com"} and len(segments) >= 3 and segments[1] == "status":
        slug = sanitize(f"{segments[0]}-post-{segments[2]}")
    else:
        first_label = host.split(".")[0] if host else ""
        slug = sanitize("-".join(part for part in [first_label, *segments[:2]] if part))
    return slug[:60].strip("-") or "deck"


def ensure_unique_slug(base: str) -> str:
    root = project_lookup_root()
    slug = base
    counter = 2
    while (root / slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def validate_deck_source_url(url: object) -> str:
    text = str(url or "").strip()
    if not text:
        raise ValueError("Thiếu link nguồn.")
    if len(text) > 2000:
        raise ValueError("Link nguồn quá dài (tối đa 2000 ký tự).")
    if any(ch.isspace() or ord(ch) < 32 for ch in text):
        raise ValueError("Link nguồn chứa ký tự không hợp lệ.")
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Link nguồn phải là địa chỉ http(s):// đầy đủ.")
    return text


def deck_tool_commands(slug: str, container_tools: bool) -> tuple[str, str, str]:
    """Trả (tools_note, validate_cmd, capture_cmd) theo môi trường chạy codex."""
    if container_tools:
        tools_note = (
            f"Môi trường tool: slide/ trên host được bind mount vào container Docker \"{DECK_CONTAINER_NAME}\" "
            "tại /app/slide — file ghi ở host thấy ngay trong container và ngược lại. Host KHÔNG có Playwright, "
            "nên validate/capture phải chạy qua docker exec đúng như lệnh đã cho. "
            f"Ảnh QA xem trực tiếp tại slide/{slug}/qa/ trên host.\n"
        )
        validate_cmd = f"docker exec {DECK_CONTAINER_NAME} python validate_slide.py /app/slide/{slug} --semantic-report"
        capture_cmd = f"docker exec {DECK_CONTAINER_NAME} python capture_slides.py /app/slide/{slug} --out /app/slide/{slug}/qa"
    else:
        tools_note = ""
        validate_cmd = f".venv/bin/python validate_slide.py slide/{slug} --semantic-report"
        capture_cmd = f".venv/bin/python capture_slides.py slide/{slug} --out slide/{slug}/qa"
    return tools_note, validate_cmd, capture_cmd


def build_deck_prompt(
    url: str,
    style: str,
    slug: str,
    notes: str,
    container_tools: bool = False,
    fixed_lines: list[str] | None = None,
) -> str:
    if fixed_lines:
        numbered = "\n".join(f"{index + 1}. {line}" for index, line in enumerate(fixed_lines))
        style_instruction = (
            "Script đã được user chốt ở wizard. Ghi slide/"
            f"{slug}/script-90s.txt NGUYÊN VĂN các dòng sau (1 dòng = 1 slide, không viết lại, không đổi số dòng):\n"
            f"{numbered}\n"
            "Dòng cuối cùng trong danh sách trên là câu outro cố định: map nó vào slide outro có sẵn trong starter (marker data-outro), không tạo slide mới cho nó.\n"
            f"Source đã được thu sẵn ở slide/{slug}/source/ từ bước drafts — kiểm tra và dùng lại, chỉ thu bổ sung nếu thiếu."
        )
    else:
        style_entry = next((item for item in DECK_STYLES if item["value"] == style), DECK_STYLES[0])
        style_instruction = style_entry["prompt"]
    notes_block = ""
    if notes:
        notes_block = f"Ghi chú thêm từ user (ưu tiên làm theo nếu không mâu thuẫn workflow):\n{notes}\n"
    tools_note, validate_cmd, capture_cmd = deck_tool_commands(slug, container_tools)
    return DECK_PROMPT_TEMPLATE.format(
        url=url,
        slug=slug,
        style_instruction=style_instruction,
        notes_block=notes_block,
        tools_note=tools_note,
        validate_cmd=validate_cmd,
        capture_cmd=capture_cmd,
    )


def build_deck_stage_prompt(
    stage: str,
    url: str,
    style: str,
    slug: str,
    notes: str,
    lines: list[str] | None,
    container_tools: bool,
) -> str:
    if stage == "drafts":
        notes_block = ""
        if notes:
            notes_block = f"Ghi chú thêm từ user (ưu tiên làm theo nếu không mâu thuẫn workflow):\n{notes}\n"
        return DECK_DRAFTS_PROMPT_TEMPLATE.format(url=url, slug=slug, notes_block=notes_block)
    if stage == "revise":
        tools_note, validate_cmd, capture_cmd = deck_tool_commands(slug, container_tools)
        return DECK_REVISE_PROMPT_TEMPLATE.format(
            slug=slug,
            notes=notes,
            tools_note=tools_note,
            validate_cmd=validate_cmd,
            capture_cmd=capture_cmd,
        )
    # auto / build dùng chung template Link Autopilot; build kèm script đã chốt
    return build_deck_prompt(url, style, slug, notes, container_tools=container_tools, fixed_lines=lines)


def deck_drafts_path(slug: str) -> Path:
    return project_lookup_root() / slug / "source" / "script-drafts.json"


def read_deck_drafts(slug: str) -> list[dict]:
    try:
        data = json.loads(deck_drafts_path(slug).read_text(encoding="utf-8"))
    except Exception:
        return []
    drafts = data.get("drafts") if isinstance(data, dict) else None
    if not isinstance(drafts, list):
        return []
    cleaned = []
    for item in drafts:
        if not isinstance(item, dict):
            continue
        lines = [str(line).strip() for line in item.get("lines") or [] if str(line).strip()]
        if not lines:
            continue
        cleaned.append(
            {
                "style": str(item.get("style") or ""),
                "label": str(item.get("label") or item.get("style") or ""),
                "hook": str(item.get("hook") or lines[0]),
                "lines": lines,
            }
        )
    return cleaned


def deck_pending_drafts() -> list[dict]:
    """Các slug đã có script-drafts.json nhưng chưa build xong deck — để UI resume wizard."""
    root = project_lookup_root()
    if not root.is_dir():
        return []
    pending = []
    for drafts_file in sorted(root.glob("*/source/script-drafts.json")):
        project_dir = drafts_file.parent.parent
        if (project_dir / "index.html").exists():
            continue
        pending.append({"slug": project_dir.name, "updated_at": drafts_file.stat().st_mtime})
    return pending


def build_deck_command(config: dict) -> list[str]:
    binary = codex_binary_path(config)
    if not binary:
        raise RuntimeError(deck_unavailable_message("codex-missing"))
    sandbox = str(config.get("sandbox") or "workspace-write")
    cmd = [binary, "exec", "--cd", str(REPO_ROOT), "--sandbox", sandbox]
    if sandbox == "workspace-write" and config.get("network_access", True):
        cmd += ["-c", "sandbox_workspace_write.network_access=true"]
    cmd += ["--color", "never", "--skip-git-repo-check"]
    model = str(config.get("model") or "").strip()
    if model:
        cmd += ["-m", model]
    effort = str(config.get("reasoning_effort") or "").strip()
    if effort:
        cmd += ["-c", f"model_reasoning_effort={effort}"]
    extra_args = config.get("extra_args")
    if isinstance(extra_args, list):
        cmd += [str(arg) for arg in extra_args]
    cmd.append("-")
    return cmd


def deck_lock_path() -> Path:
    return project_lookup_root() / ".deck-job.json"


def read_deck_lock() -> dict | None:
    try:
        data = json.loads(deck_lock_path().read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def write_deck_lock(job_id: str, pid: int, slug: str) -> None:
    payload = {"job_id": job_id, "pid": pid, "slug": slug, "started_at": time.time()}
    try:
        deck_lock_path().write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def clear_deck_lock() -> None:
    try:
        deck_lock_path().unlink(missing_ok=True)
    except Exception:
        pass


def pid_alive(pid: object) -> bool:
    try:
        os.kill(int(pid), 0)
    except (OSError, TypeError, ValueError):
        return False
    return True


def finish_deck_job_cleanup(job_id: str) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        timer = job.get("timer") if job else None
        job_type = job.get("job_type") if job else None
        if job is not None:
            job["timer"] = None
    if timer is not None:
        try:
            timer.cancel()
        except Exception:
            pass
    if job_type == "deck":
        clear_deck_lock()


def active_deck_job() -> dict | None:
    with JOBS_LOCK:
        for job in JOBS.values():
            if job.get("job_type") == "deck" and job.get("status") in ACTIVE_JOB_STATUSES:
                return public_job(job)
    return None


def deck_status_payload() -> dict:
    config = load_agent_config()
    available, reason, mode = deck_feature_state(config)
    active = active_deck_job()
    stale = None
    if not active:
        lock = read_deck_lock()
        if lock and pid_alive(lock.get("pid")):
            stale = {"pid": lock.get("pid"), "slug": lock.get("slug"), "job_id": lock.get("job_id")}
    return {
        "available": available,
        "reason": reason,
        "mode": mode,
        "codex_path": codex_binary_path(config),
        "runner_connected": deck_runner_heartbeat_fresh(),
        "styles": [{"value": item["value"], "label": item["label"]} for item in DECK_STYLES],
        "active_job": active,
        "stale_lock": stale,
        "pending_drafts": deck_pending_drafts(),
    }


def deck_job_timeout(job_id: str, timeout_minutes: int) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job or job.get("status") not in ACTIVE_JOB_STATUSES:
            return
        job["cancel_requested"] = True
        job["timeout_hit"] = True
        job["updated_at"] = time.time()
        proc = job.get("process")
    append_log(job_id, f"\nDeck build vượt quá {timeout_minutes} phút, tự dừng.\n")
    if isinstance(proc, subprocess.Popen):
        terminate_process(proc)
    set_job_state(
        job_id,
        status="failed",
        error=f"Deck build vượt quá {timeout_minutes} phút, đã dừng.",
        finished_at=time.time(),
    )
    clear_deck_lock()


def deck_failure_summary(logs: str, slug: str, returncode: int | None) -> str:
    text = str(logs or "")
    failed_lines = re.findall(r"DECK_BUILD: FAILED.*", text)
    if failed_lines:
        summary = failed_lines[-1].replace("DECK_BUILD: FAILED", "").strip() or "Agent báo thất bại."
    else:
        deck_dir = project_lookup_root() / slug
        if not (deck_dir / "index.html").exists():
            summary = f"Codex chạy xong nhưng thiếu slide/{slug}/index.html."
        elif not (deck_dir / "script-90s.txt").exists():
            summary = f"Codex chạy xong nhưng thiếu slide/{slug}/script-90s.txt."
        elif not list((deck_dir / "qa").glob("*.png")):
            summary = f"Codex chạy xong nhưng không có ảnh QA trong slide/{slug}/qa/."
        else:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            summary = lines[-1] if lines else f"Deck build thất bại (exit code {returncode})."
    if re.search(r"Operation not permitted|sandbox|seatbelt", text, re.IGNORECASE) and re.search(
        r"playwright|chromium", text, re.IGNORECASE
    ):
        summary += ' Có thể sandbox chặn Chromium — thử "sandbox": "danger-full-access" trong config/agent.json.'
    return summary


def deck_qa_pngs(deck_dir: Path) -> list[Path]:
    def natural_key(path: Path) -> list[object]:
        return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]

    return sorted((deck_dir / "qa").glob("*.png"), key=natural_key)


def finalize_deck_job(job_id: str, slug: str, returncode: int | None) -> None:
    with JOBS_LOCK:
        logs = str((JOBS.get(job_id) or {}).get("logs") or "")
    deck_dir = project_lookup_root() / slug
    qa_pngs = deck_qa_pngs(deck_dir)
    success = (
        returncode == 0
        and (deck_dir / "index.html").exists()
        and (deck_dir / "script-90s.txt").exists()
        and bool(qa_pngs)
        and "DECK_BUILD: FAILED" not in logs
    )
    if not success:
        summary = deck_failure_summary(logs, slug, returncode)
        append_log(job_id, f"\nDeck build thất bại: {summary}\n")
        set_job_state(job_id, status="failed", returncode=returncode, finished_at=time.time(), error=summary)
        return

    warnings = []
    if not (deck_dir / "preview-assets" / "bgm" / "meta.mp3").exists():
        warnings.append(
            "Deck chưa có nhạc nền (preview-assets/bgm/meta.mp3) — video sẽ render KHÔNG có BGM. "
            "Đặt file meta.mp3 vào template/nicetechchannels-slide-starter/preview-assets/bgm/ một lần "
            "để các deck sau tự có, hoặc upload BGM trong panel cài đặt của trang preview deck."
        )
    if "DECK_BUILD: SUCCESS" not in logs:
        warnings.append("Agent không in marker DECK_BUILD: SUCCESS — kiểm tra deck kỹ hơn trước khi render.")
    qa_urls = [f"/slide/{quote(slug)}/qa/{quote(path.name)}" for path in qa_pngs]
    append_log(job_id, f"\nDeck sẵn sàng: slide/{slug}/ ({len(qa_urls)} ảnh QA)\n")
    set_job_state(
        job_id,
        status="done",
        returncode=returncode,
        finished_at=time.time(),
        qa_urls=qa_urls,
        deck_url=project_url(slug),
        warnings=warnings,
    )


def finalize_drafts_job(job_id: str, slug: str, returncode: int | None) -> None:
    with JOBS_LOCK:
        logs = str((JOBS.get(job_id) or {}).get("logs") or "")
    drafts = read_deck_drafts(slug)
    success = returncode == 0 and bool(drafts) and "DECK_DRAFTS: FAILED" not in logs
    if not success:
        failed_lines = re.findall(r"DECK_DRAFTS: FAILED.*", logs)
        if failed_lines:
            summary = failed_lines[-1].replace("DECK_DRAFTS: FAILED", "").strip() or "Agent báo thất bại."
        elif not drafts:
            summary = f"Codex chạy xong nhưng thiếu hoặc hỏng slide/{slug}/source/script-drafts.json."
        else:
            log_lines = [line.strip() for line in logs.splitlines() if line.strip()]
            summary = log_lines[-1] if log_lines else f"Viết nháp script thất bại (exit code {returncode})."
        append_log(job_id, f"\nViết nháp script thất bại: {summary}\n")
        set_job_state(job_id, status="failed", returncode=returncode, finished_at=time.time(), error=summary)
        return

    warnings = []
    if len(drafts) < 5:
        warnings.append(f"Chỉ có {len(drafts)}/5 bản nháp hợp lệ trong script-drafts.json.")
    append_log(job_id, f"\nĐã có {len(drafts)} bản nháp script cho slide/{slug}/ — chờ user chọn.\n")
    set_job_state(
        job_id,
        status="done",
        returncode=returncode,
        finished_at=time.time(),
        drafts=drafts,
        warnings=warnings,
    )


def finalize_deck_stage(job_id: str, slug: str, returncode: int | None) -> None:
    if job_field(job_id, "stage") == "drafts":
        finalize_drafts_job(job_id, slug, returncode)
    else:
        finalize_deck_job(job_id, slug, returncode)


def record_deck_run_cost(job_id: str, slug: str, returncode: int) -> None:
    """Ghi event codex_run vào cost-ledger sau khi codex exec (local mode) kết thúc. Không raise."""
    try:
        with JOBS_LOCK:
            job = JOBS.get(job_id) or {}
            logs = str(job.get("logs") or "")
            stage = str(job.get("stage") or "auto")
            notes = str(job.get("notes") or "")
            started_at = job.get("started_at")
            session_id = job.get("codex_session_id")
            cancelled = bool(job.get("cancel_requested"))
        config = load_agent_config()
        session_id = session_id or cost_tracking.parse_session_id(logs)
        tokens = cost_tracking.parse_token_usage(logs)
        tokens_source = "stdout" if tokens else "missing"
        model = str(config.get("model") or "").strip()
        if tokens is None or not model:
            # Job bị cancel/timeout thì codex không in dòng Token usage -> đọc rollout theo session id
            rollout = cost_tracking.find_rollout_file(session_id)
            parsed = cost_tracking.parse_rollout(rollout) if rollout else None
            if parsed:
                if tokens is None and parsed.get("tokens"):
                    tokens = parsed["tokens"]
                    tokens_source = "rollout"
                model = model or str(parsed.get("model") or "")
        model = model or cost_tracking.parse_model_line(logs) or "unknown"
        duration_s = round(time.time() - started_at, 1) if isinstance(started_at, (int, float)) else None
        project_dir = project_lookup_root() / slug
        cost_tracking.safe_append_event(project_dir, {
            "type": "codex_run",
            "writer": "web_server",
            "job_id": job_id,
            "stage": stage,
            "mode": "local",
            "model": model,
            "reasoning_effort": str(config.get("reasoning_effort") or ""),
            "tokens": tokens,
            "tokens_source": tokens_source,
            "session_id": session_id,
            "usd": cost_tracking.codex_usd(tokens, model, cost_tracking.load_pricing()),
            "duration_s": duration_s,
            "returncode": returncode,
            "cancelled": cancelled,
            "slide_count": cost_tracking.count_script_lines(project_dir),
            "notes": notes,
            "usage_missing": tokens is None,
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[cost] Không ghi được codex_run cho job {job_id}: {exc}")


def record_deck_run_cost_from_runner(job_id: str, slug: str, status: dict) -> None:
    """Ghi event codex_run từ status.json của host runner — phải gọi TRƯỚC khi cleanup xoá file job."""
    try:
        with JOBS_LOCK:
            job = JOBS.get(job_id) or {}
            logs = str(job.get("logs") or "")
            stage = str(job.get("stage") or "auto")
            notes = str(job.get("notes") or "")
            started_at = job.get("started_at")
            cancelled = bool(job.get("cancel_requested"))
        config = load_agent_config()
        tokens = status.get("usage") if isinstance(status.get("usage"), dict) else None
        tokens_source = str(status.get("tokens_source") or "")
        if tokens is None:
            # Runner cũ chưa ghi usage vào status.json: dòng Token usage nằm cuối log nên sống sót cắt 240k
            tokens = cost_tracking.parse_token_usage(logs)
            tokens_source = "stdout" if tokens else "missing"
        session_id = status.get("session_id") or cost_tracking.parse_session_id(logs)
        model = (
            str(status.get("model") or "")
            or str(config.get("model") or "").strip()
            or cost_tracking.parse_model_line(logs)
            or "unknown"
        )
        returncode = status.get("returncode")
        duration_s = round(time.time() - started_at, 1) if isinstance(started_at, (int, float)) else None
        project_dir = project_lookup_root() / slug
        cost_tracking.safe_append_event(project_dir, {
            "type": "codex_run",
            "writer": "web_server",
            "job_id": job_id,
            "stage": stage,
            "mode": "runner",
            "model": model,
            "reasoning_effort": str(config.get("reasoning_effort") or ""),
            "tokens": tokens,
            "tokens_source": tokens_source,
            "session_id": session_id,
            "usd": cost_tracking.codex_usd(tokens, model, cost_tracking.load_pricing()),
            "duration_s": duration_s,
            "returncode": returncode if isinstance(returncode, int) else -1,
            "cancelled": cancelled,
            "slide_count": cost_tracking.count_script_lines(project_dir),
            "notes": notes,
            "usage_missing": tokens is None,
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[cost] Không ghi được codex_run (runner) cho job {job_id}: {exc}")


def create_deck_job(payload: dict) -> dict:
    config = load_agent_config()
    available, reason, mode = deck_feature_state(config)
    if not available:
        raise RuntimeError(deck_unavailable_message(reason))

    stage = str(payload.get("stage") or "auto").strip() or "auto"
    if stage not in {"auto", "drafts", "build", "revise"}:
        raise ValueError(f"Stage không hợp lệ: {stage}")

    style = str(payload.get("style") or "auto").strip() or "auto"
    if style not in {item["value"] for item in DECK_STYLES}:
        raise ValueError(f"Style không hợp lệ: {style}")

    notes = str(payload.get("notes") or "").strip()[:2000]
    if stage in {"auto", "drafts"}:
        url = validate_deck_source_url(payload.get("url"))
    else:
        url = str(payload.get("url") or "").strip()[:2000]

    root = project_lookup_root()
    requested_slug = str(payload.get("slug") or "").strip().lower()
    if requested_slug and not DECK_SLUG_RE.match(requested_slug):
        raise ValueError("Slug chỉ gồm a-z, 0-9 và dấu gạch ngang, dài 2-63 ký tự, bắt đầu bằng chữ/số.")

    if stage in {"build", "revise"}:
        if not requested_slug:
            raise ValueError("Thiếu slug project cho bước này.")
        slug = requested_slug
        if stage == "build" and not (root / slug / "source").is_dir():
            raise RuntimeError(f"Chưa có slide/{slug}/source/ — chạy bước viết nháp script trước.")
        if stage == "revise" and not (root / slug / "index.html").exists():
            raise RuntimeError(f"slide/{slug}/ chưa phải deck hoàn chỉnh để sửa.")
    elif requested_slug:
        existing = root / requested_slug
        if (existing / "index.html").exists():
            raise RuntimeError(f"Slug '{requested_slug}' đã là deck hoàn chỉnh trong slide/.")
        if stage == "auto" and existing.exists():
            raise RuntimeError(f"Slug '{requested_slug}' đã tồn tại trong slide/.")
        slug = requested_slug
    else:
        slug = ensure_unique_slug(derive_deck_slug(url))

    lines = None
    if stage == "build":
        raw_lines = payload.get("lines")
        if not isinstance(raw_lines, list) or not raw_lines:
            raise ValueError("Thiếu script đã chốt (lines).")
        lines = [str(line).strip() for line in raw_lines]
        if any(not line for line in lines):
            raise ValueError("Script có dòng trống.")
        if len(lines) > 20 or any(len(line) > 600 for line in lines):
            raise ValueError("Script quá dài (tối đa 20 dòng, 600 ký tự mỗi dòng).")
        # Dòng outro cố định luôn do server append làm dòng cuối; bỏ bản user paste kèm để tránh outro kép.
        outro_norm = social_metadata.normalized_script_line(social_metadata.OUTRO_SCRIPT_LINE)
        brand_norm = social_metadata.normalized_script_line(social_metadata.BRANDING["name"])
        while lines:
            last_norm = social_metadata.normalized_script_line(lines[-1])
            if last_norm == outro_norm or (
                brand_norm in last_norm and ("đăng ký" in last_norm or "theo dõi" in last_norm)
            ):
                lines.pop()
                continue
            break
        if not lines:
            raise ValueError("Script chỉ có dòng outro, thiếu nội dung.")
        lines.append(social_metadata.OUTRO_SCRIPT_LINE)
    if stage == "revise" and not notes:
        raise ValueError("Nhập yêu cầu sửa trước khi gửi.")

    if active_deck_job():
        raise RuntimeError("Đang có deck job chạy. Chờ xong hoặc bấm Dừng job cũ trước.")

    prompt = build_deck_stage_prompt(stage, url, style, slug, notes, lines, container_tools=(mode == "runner"))

    if mode == "runner":
        return create_deck_job_via_runner(config, url, style, slug, stage, prompt, bool(payload.get("force")), notes)

    lock = read_deck_lock()
    if lock:
        alive = pid_alive(lock.get("pid"))
        if alive and not payload.get("force"):
            raise RuntimeError(
                f"Có deck job mồ côi từ lần chạy server trước (pid {lock.get('pid')}, slug {lock.get('slug')}). "
                f"Dừng nó bằng: kill -TERM -{lock.get('pid')}, hoặc gửi lại với force=true."
            )
        clear_deck_lock()

    try:
        timeout_minutes = max(5, int(config.get("timeout_minutes")))
    except (TypeError, ValueError):
        timeout_minutes = int(DECK_DEFAULT_AGENT_CONFIG["timeout_minutes"])

    cmd = build_deck_command(config)
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    job = {
        "id": job_id,
        "project": slug,
        "job_type": "deck",
        "stage": stage,
        "engine": "codex",
        "status": "queued",
        "logs": "",
        "created_at": now,
        "updated_at": now,
        "video_url": None,
        "source_url": url,
        "style": style,
        "notes": notes,
        "qa_urls": [],
        "deck_url": None,
        "warnings": [],
    }
    with JOBS_LOCK:
        JOBS[job_id] = job

    timer = threading.Timer(timeout_minutes * 60, deck_job_timeout, args=(job_id, timeout_minutes))
    timer.daemon = True
    set_job_state(job_id, timer=timer)
    timer.start()

    thread = threading.Thread(target=run_job, args=(job_id, cmd, slug), kwargs={"stdin_data": prompt}, daemon=True)
    thread.start()
    return public_job(job)


def create_deck_job_via_runner(config: dict, url: str, style: str, slug: str, stage: str, prompt: str, force: bool, notes: str = "") -> dict:
    running_ids = deck_runner_running_job_ids()
    if running_ids and not force:
        raise RuntimeError(
            f"Host runner đang chạy deck job khác ({', '.join(running_ids)}). "
            "Chờ xong hoặc gửi lại với force=true để yêu cầu dừng job cũ."
        )
    for old_id in running_ids:
        try:
            deck_runner_job_paths(old_id)["cancel"].write_text("cancel", encoding="utf-8")
        except OSError:
            pass

    try:
        timeout_minutes = max(5, int(config.get("timeout_minutes")))
    except (TypeError, ValueError):
        timeout_minutes = int(DECK_DEFAULT_AGENT_CONFIG["timeout_minutes"])

    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    job = {
        "id": job_id,
        "project": slug,
        "job_type": "deck",
        "stage": stage,
        "engine": "codex",
        "runner": True,
        "status": "queued",
        "logs": "",
        "created_at": now,
        "updated_at": now,
        "video_url": None,
        "source_url": url,
        "style": style,
        "notes": notes,
        "qa_urls": [],
        "deck_url": None,
        "warnings": [],
    }
    with JOBS_LOCK:
        JOBS[job_id] = job

    jobs_root = deck_runner_jobs_root()
    jobs_root.mkdir(parents=True, exist_ok=True)
    paths = deck_runner_job_paths(job_id)
    request = {
        "job_id": job_id,
        "slug": slug,
        "stage": stage,
        "prompt": prompt,
        "timeout_minutes": timeout_minutes,
        "created_at": now,
    }
    tmp_path = paths["request"].with_suffix(".tmp")
    tmp_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    tmp_path.rename(paths["request"])
    append_log(job_id, f"Đã gửi yêu cầu cho host runner ({len(prompt)} ký tự prompt, timeout {timeout_minutes} phút).\n")

    thread = threading.Thread(target=run_deck_via_runner, args=(job_id, slug, timeout_minutes), daemon=True)
    thread.start()
    return public_job(job)


def run_deck_via_runner(job_id: str, slug: str, timeout_minutes: int) -> None:
    paths = deck_runner_job_paths(job_id)
    deadline = time.time() + timeout_minutes * 60
    log_offset = 0
    started = False
    cancel_sent = False
    heartbeat_lost_since = None
    try:
        while True:
            time.sleep(1.0)

            try:
                with paths["log"].open("r", encoding="utf-8", errors="replace") as fh:
                    fh.seek(log_offset)
                    chunk = fh.read()
                    log_offset = fh.tell()
                if chunk:
                    append_log(job_id, chunk)
            except OSError:
                pass

            status = deck_runner_read_status(job_id)
            if status and status.get("status") == "running" and not started:
                started = True
                set_job_state(
                    job_id,
                    status="running",
                    started_at=time.time(),
                    command=f"codex exec (host runner, pid {status.get('pid')})",
                )
            if status and status.get("status") == "exited":
                # Ghi cost TRƯỚC mọi nhánh kết thúc: finally bên dưới xoá status.json/log ngay khi job terminal.
                record_deck_run_cost_from_runner(job_id, slug, status)
                returncode = status.get("returncode")
                returncode = returncode if isinstance(returncode, int) else -1
                if job_cancel_requested(job_id):
                    if job_field(job_id, "timeout_hit"):
                        set_job_state(
                            job_id,
                            status="failed",
                            returncode=returncode,
                            finished_at=time.time(),
                            error=f"Deck build vượt quá {timeout_minutes} phút, đã dừng.",
                        )
                    else:
                        append_log(job_id, "\nĐã dừng theo yêu cầu.\n")
                        set_job_state(job_id, status="cancelled", returncode=returncode, finished_at=time.time())
                else:
                    finalize_deck_stage(job_id, slug, returncode)
                return

            if time.time() > deadline and not job_field(job_id, "timeout_hit"):
                set_job_state(job_id, timeout_hit=True, cancel_requested=True)
                append_log(job_id, f"\nDeck build vượt quá {timeout_minutes} phút, gửi tín hiệu dừng cho runner.\n")
            if job_cancel_requested(job_id) and not cancel_sent:
                try:
                    paths["cancel"].write_text("cancel", encoding="utf-8")
                    cancel_sent = True
                except OSError:
                    pass

            if not deck_runner_heartbeat_fresh():
                if heartbeat_lost_since is None:
                    heartbeat_lost_since = time.time()
                elif time.time() - heartbeat_lost_since > 60:
                    append_log(job_id, "\nMất kết nối host runner (heartbeat dừng hơn 60 giây).\n")
                    set_job_state(
                        job_id,
                        status="failed",
                        finished_at=time.time(),
                        error="Mất kết nối host runner. Kiểm tra deck_host_runner.py trên host rồi thử lại.",
                    )
                    return
            else:
                heartbeat_lost_since = None
    finally:
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            terminal = bool(job and job.get("status") in {"done", "failed", "cancelled"})
        if terminal:
            for key in ("request", "status", "log", "cancel"):
                try:
                    paths[key].unlink(missing_ok=True)
                except OSError:
                    pass


def delete_project_output(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    confirm = bool(payload.get("confirm"))
    if not confirm:
        raise ValueError("Missing delete confirmation.")
    if has_running_job(project):
        raise RuntimeError(f"Project '{project}' has a running render job.")

    project_dir = require_slide_project(project)
    output_dir = (project_dir / "output").resolve()
    try:
        output_dir.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid output path.") from exc
    if output_dir.name != "output":
        raise ValueError("Refusing to delete a non-output directory.")

    existed = output_dir.is_dir() and any(output_dir.iterdir())
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("Output path exists but is not a directory.")
    paid_voiceover = output_dir / "elevenlabs_full_voiceover.mp3"
    paid_files = [name for name in (paid_voiceover.name, "elevenlabs_full_voiceover.meta.json") if (output_dir / name).exists()]
    if existed:
        shutil.rmtree(output_dir)
        # Ghi lại việc audio trả phí bị xoá: lần render sau ElevenLabs sẽ bill lại cả deck.
        cost_tracking.safe_append_event(project_dir, {
            "type": "output_delete",
            "writer": "web_server",
            "had_paid_voiceover": bool(paid_files),
            "files_lost": paid_files,
        })

    return {
        "ok": True,
        "project": project_dir.name,
        "deleted": existed,
        "output_url": final_video_url(project_dir.name),
    }


def reveal_project_output(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    project_dir = require_slide_project(project)
    output_dir = (project_dir / "output").resolve()
    video_path = (output_dir / "final_video.mp4").resolve()
    try:
        output_dir.relative_to(project_dir.resolve())
        video_path.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid output path.") from exc
    if not video_path.is_file():
        raise FileNotFoundError(f"final_video.mp4 not found for project '{project_dir.name}'.")

    if sys.platform == "darwin":
        cmd = ["open", "-R", str(video_path)]
    elif sys.platform.startswith("win"):
        cmd = ["explorer", f"/select,{video_path}"]
    else:
        opener = shutil.which("xdg-open")
        if not opener:
            raise RuntimeError("No supported file manager opener found.")
        cmd = [opener, str(output_dir)]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {
        "ok": True,
        "project": project_dir.name,
        "path": str(video_path),
        "output_dir": str(output_dir),
    }




def social_callback_html(title: str, message: str, ok: bool = True) -> bytes:
    color = "#f2b261" if ok else "#ff8585"
    return f"""<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>{html.escape(title)}</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#070b0a;color:#eefcf4;padding:32px;">
  <main style="max-width:680px;margin:0 auto;border:1px solid rgba(255,255,255,.14);border-radius:20px;padding:24px;background:rgba(255,255,255,.06);">
    <h1 style="margin-top:0;color:{color};">{html.escape(title)}</h1>
    <p style="line-height:1.6;">{html.escape(message)}</p>
    <p style="opacity:.72;">Bạn có thể đóng tab này và quay lại {html.escape(branding.BRANDING['name'])} Upload Center.</p>
  </main>
</body>
</html>""".encode("utf-8")


def render_elevenlabs_guide_html() -> bytes:
    return render_page_shell(
        title="Hướng dẫn ElevenLabs",
        body="""
  <main class="guide-page">
    <header class="guide-hero">
      <a class="small-link back-link" href="/">← Quay lại Web UI</a>
      <h1>Hướng dẫn ElevenLabs</h1>
      <p>Dùng cách thủ công khi bạn muốn tự nghe và tải file audio. Dùng API khi muốn Web UI tự gọi ElevenLabs rồi render luôn.</p>
      <div class="guide-links">
        <a href="https://elevenlabs.io/app/speech-synthesis/text-to-speech" target="_blank" rel="noreferrer">Mở ElevenLabs Dashboard</a>
        <a class="small-link" href="https://elevenlabs.io/app/voice-library?search=nh%E1%BA%ADt+" target="_blank" rel="noreferrer">Mở Voice Library</a>
        <a class="small-link" href="https://elevenlabs.io/app/subscription/api" target="_blank" rel="noreferrer">Nạp API credit</a>
        <a class="small-link" href="https://elevenlabs.io/app/developers/api-keys" target="_blank" rel="noreferrer">Tạo API key</a>
      </div>
    </header>

    <section class="guide-card" id="manual">
      <div class="guide-copy">
        <p class="kicker">Tải file audio</p>
        <h2>Cách làm thủ công</h2>
        <ol>
          <li class="guide-action-step"><span>Đăng ký tài khoản ElevenLabs.</span><a href="https://try.elevenlabs.io/z38mu0hfbskn" target="_blank" rel="noreferrer">Mở Trang Đăng ký</a></li>
          <li>Bấm mở ElevenLabs Dashboard.</li>
          <li>Dán toàn bộ `script-90s.txt` vào vùng nhập chữ.</li>
          <li>Chọn voice “Nhật - Narrative & Compelling”.</li>
          <li>Chọn model Eleven v3, generate rồi tải audio về.</li>
          <li>Quay lại Web UI, chọn file audio và render.</li>
        </ol>
      </div>
      <div class="guide-shot tts-shot" aria-label="Hướng dẫn ElevenLabs Text to Speech">
        <div class="shot-sidebar"><strong>ElevenLabs</strong><span>Text to Speech</span><span>Voices</span><span>Studio</span></div>
        <div class="shot-main">
          <div class="shot-top">Text to Speech</div>
          <div class="script-zone callout script-callout">
            <span class="voice-pill callout voice-callout">Nhật - Narrative & Compelling</span>
            <p>Dán script-90s.txt vào đây</p>
          </div>
        </div>
        <div class="shot-settings">
          <strong>Settings</strong>
          <div class="setting-row callout voice-callout">Voice: Nhật...</div>
          <div class="setting-row callout model-callout">Model: Eleven v3</div>
          <div class="setting-row">Output: MP3 44.1kHz</div>
        </div>
        <div class="note-pin note-script">Dán script</div>
        <div class="note-pin note-voice">Voice Nhật</div>
        <div class="note-pin note-model">Model v3</div>
      </div>
      <a href="https://elevenlabs.io/app/speech-synthesis/text-to-speech" target="_blank" rel="noreferrer">Mở ElevenLabs Dashboard</a>
    </section>

    <section class="guide-card" id="api-credit">
      <div class="guide-copy">
        <p class="kicker">ElevenLabs API</p>
        <h2>Nạp credit trước khi test</h2>
        <ol>
          <li class="guide-action-step"><span>Đăng ký tài khoản ElevenLabs.</span><a href="https://try.elevenlabs.io/z38mu0hfbskn" target="_blank" rel="noreferrer">Mở Trang Đăng ký</a></li>
          <li>Vào trang ElevenAPI subscription.</li>
          <li>Bấm Add credits.</li>
          <li>Nạp khoảng 5 đô để test trước, đừng nạp nhiều khi chưa rõ workflow.</li>
        </ol>
      </div>
      <div class="guide-shot billing-shot" aria-label="Hướng dẫn nạp credit ElevenLabs API">
        <div class="shot-sidebar"><strong>ElevenLabs</strong><span>Home</span><span>Text to Speech</span><span>Developers</span></div>
        <div class="billing-main">
          <h3>Subscription</h3>
          <div class="billing-tabs"><span>ElevenCreative</span><span class="active">ElevenAPI</span></div>
          <div class="balance-box">
            <span>Top up balance</span>
            <strong>$2.43</strong>
            <button class="callout credit-callout">+ Add credits</button>
          </div>
          <div class="pricing-row"><span>Multilingual v2 / v3</span><b>$0.10</b><small>per 1K characters</small></div>
        </div>
        <div class="note-pin note-credit">Nạp $5 để test</div>
      </div>
      <a href="https://elevenlabs.io/app/subscription/api" target="_blank" rel="noreferrer">Mở trang nạp API credit</a>
    </section>

    <section class="guide-card" id="api-key">
      <div class="guide-copy">
        <p class="kicker">API key</p>
        <h2>Tạo key rồi lưu vào Web UI</h2>
        <ol>
          <li>Vào Developers → API Keys.</li>
          <li>Bấm Create Key.</li>
          <li>Copy key, quay lại Web UI và dán vào ô ElevenLabs API key.</li>
        </ol>
      </div>
      <div class="guide-shot api-shot" aria-label="Hướng dẫn tạo ElevenLabs API key">
        <div class="shot-sidebar"><strong>ElevenLabs</strong><span>Home</span><span>Text to Speech</span><span>Developers</span></div>
        <div class="api-main">
          <h3>Developers</h3>
          <div class="api-tabs"><span>Overview</span><span class="active">API Keys</span><span>Webhooks</span><span>Analytics</span></div>
          <p>An API key lets you connect to the API.</p>
          <button class="callout key-callout">+ Create Key</button>
          <div class="key-row"><span>main</span><span>••••••••••••a283</span><span>Enabled</span></div>
        </div>
        <div class="note-pin note-key">Tạo API key</div>
      </div>
      <a href="https://elevenlabs.io/app/developers/api-keys" target="_blank" rel="noreferrer">Mở trang tạo API key</a>
    </section>

    <section class="guide-card" id="voice-id">
      <div class="guide-copy">
        <p class="kicker">Voice Library</p>
        <h2>Lấy Voice ID của giọng Nhật</h2>
        <ol>
          <li>Mở Voice Library với từ khóa “nhật” đã điền sẵn.</li>
          <li>Tìm dòng “Nhật - Narrative & Compelling”.</li>
          <li>Bấm menu ba chấm rồi chọn Copy voice ID.</li>
          <li>Quay lại Web UI, dán vào ô Voice ID trong phần nâng cao.</li>
        </ol>
      </div>
      <div class="guide-shot voice-shot" aria-label="Hướng dẫn lấy ElevenLabs Voice ID">
        <div class="shot-sidebar"><strong>ElevenLabs</strong><span>Home</span><span class="active-side">Voices</span><span>Studio</span><span>Flows</span></div>
        <div class="voice-main">
          <div class="voice-breadcrumb">Voices › Explore</div>
          <h3>Voices</h3>
          <div class="voice-tabs"><span class="active">Explore</span><span>My Voices</span></div>
          <div class="voice-search">⌕ <span>nhật</span></div>
          <div class="voice-filters"><span>Language</span><span>Narration</span><span>Characters</span><span>Social Media</span><span>Educational</span></div>
          <p class="voice-count">2,721 voices</p>
          <div class="voice-list">
            <div class="voice-row featured">
              <div class="voice-avatar"></div>
              <div class="voice-title"><strong>Nhật - Narrative & Compelling</strong><span>Articulate Vietnamese voice suited...</span></div>
              <span>Vietnamese</span><span>Northern</span><span>45.8K</span><span>Narration</span>
              <button class="voice-dots callout voice-dots-callout" type="button">⋮</button>
            </div>
            <div class="voice-row muted-row"><div class="voice-avatar dark"></div><div class="voice-title"><strong>Finn - The British voice that makes ...</strong><span>I'm Finn, a British voice artist with...</span></div><span>English</span><span>British</span><span>15.4K</span><span>Conversational</span><button class="voice-dots" type="button">⋮</button></div>
            <div class="voice-row muted-row"><div class="voice-avatar blue"></div><div class="voice-title"><strong>Suhaan - Calm, Clear and Neat</strong><span>Suhaan - Delhi Guy - Suhan is a...</span></div><span>Hindi</span><span>Standard</span><span>44.2K</span><span>Conversational</span><button class="voice-dots" type="button">⋮</button></div>
          </div>
          <div class="voice-menu callout voice-id-callout">
            <div class="voice-copy-row">⧉ <strong>Copy voice ID</strong></div>
            <div>▱ Add to collection</div>
            <div>≋ View similar</div>
          </div>
        </div>
        <div class="note-pin note-voice-id">Khoanh chỗ lấy Voice ID</div>
      </div>
      <a href="https://elevenlabs.io/app/voice-library?search=nh%E1%BA%ADt+" target="_blank" rel="noreferrer">Mở Voice Library đã search “nhật”</a>
    </section>
  </main>
""",
        extra_style="""
    body { overflow: auto; }
    .guide-page { max-width: 1180px; margin: 0 auto; }
    .guide-hero { max-width: none; margin-bottom: 22px; }
    .guide-hero h1 {
      max-width: none;
      font-size: clamp(34px, 4vw, 54px);
      white-space: nowrap;
    }
    .back-link { margin-bottom: 18px; }
    .guide-links { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    .guide-card {
      display: grid;
      grid-template-columns: minmax(240px, 0.72fr) minmax(420px, 1.28fr);
      gap: 20px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      padding: 22px;
      background: var(--panel);
      box-shadow: var(--shadow);
      margin: 18px 0;
    }
    .guide-copy h2 { margin: 0 0 12px; font-size: clamp(26px, 3vw, 42px); letter-spacing: -0.02em; }
    .guide-copy ol { margin: 0; padding-left: 20px; color: var(--text-soft); line-height: 1.65; font-weight: 500; }
    .guide-action-step { margin-bottom: 8px; }
    .guide-action-step a {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      margin-left: 8px;
      padding: 4px 10px;
      border: 1px solid var(--accent);
      border-radius: var(--r-sm);
      color: var(--accent-contrast);
      background: var(--accent);
      font-size: 12px;
      font-weight: 600;
      line-height: 1.2;
      white-space: nowrap;
    }
    .kicker { margin: 0 0 8px; color: var(--accent); font-family: var(--font-mono); font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; }
    .guide-shot {
      position: relative;
      min-height: 360px;
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      overflow: hidden;
      background: #f7f7f7;
      color: #171717;
      box-shadow: var(--shadow);
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .shot-sidebar {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 170px;
      padding: 18px 16px;
      border-right: 1px solid #ddd;
      background: #fbfbfb;
      display: grid;
      align-content: start;
      gap: 18px;
      color: #6b6b78;
      font-weight: 700;
    }
    .shot-sidebar strong { color: #080808; font-size: 20px; }
    .shot-sidebar .active-side {
      margin-left: -8px;
      margin-right: -8px;
      padding: 8px;
      border-radius: 12px;
      background: #ededed;
      color: #151515;
    }
    .shot-main { margin-left: 170px; margin-right: 280px; min-height: 360px; padding: 18px 22px; background: #fff; }
    .shot-top { font-weight: 800; font-size: 18px; margin-bottom: 56px; }
    .script-zone {
      position: relative;
      height: 174px;
      border-radius: 18px;
      background: linear-gradient(#fff,#fff) padding-box, linear-gradient(135deg,#38bdf8,#f472b6,#fb923c) border-box;
      border: 3px solid transparent;
      padding: 24px;
    }
    .script-zone p { color: #8a8a96; font-size: 18px; margin: 24px 0 0; }
    .voice-pill { display: inline-flex; padding: 9px 13px; border: 2px solid #0f172a; border-radius: 999px; background: #fff; font-weight: 800; }
    .shot-settings {
      position: absolute;
      right: 0;
      top: 0;
      bottom: 0;
      width: 280px;
      padding: 70px 16px 18px;
      border-left: 1px solid #ddd;
      background: #fff;
      display: grid;
      align-content: start;
      gap: 14px;
    }
    .shot-settings strong { font-size: 18px; margin-bottom: 10px; }
    .setting-row { padding: 14px 12px; border: 1px solid #dedee5; border-radius: 14px; background: #fff; font-weight: 800; }
    .billing-main, .api-main { margin-left: 170px; min-height: 360px; padding: 30px; background: #fff; }
    .billing-main h3, .api-main h3 { margin: 0 0 18px; font-size: 34px; font-weight: 500; }
    .billing-tabs, .api-tabs { display: flex; gap: 18px; padding-bottom: 12px; border-bottom: 1px solid #e5e5e5; color: #777985; font-weight: 700; }
    .billing-tabs .active, .api-tabs .active { color: #111; border: 2px solid #111; border-radius: 10px; padding: 7px 12px; margin-top: -9px; }
    .balance-box { width: min(520px, 92%); margin-top: 36px; border: 1px solid #ddd; border-radius: 20px; padding: 22px; box-shadow: 0 8px 20px rgba(0,0,0,.05); }
    .balance-box span { color: #7a7d89; font-weight: 700; }
    .balance-box strong { display: block; font-size: 32px; margin: 8px 0; }
    .balance-box button, .api-main button { border: 0; border-radius: 12px; padding: 13px 18px; background: #050505; color: #fff; font-weight: 800; font-size: 17px; }
    .pricing-row { margin-top: 40px; width: 290px; border: 1px solid #e1e1e1; border-radius: 18px; padding: 22px; display: grid; gap: 14px; }
    .pricing-row b { font-size: 28px; }
    .pricing-row small { color: #7a7d89; font-size: 16px; }
    .api-main p { color: #777985; font-weight: 700; max-width: 520px; line-height: 1.5; }
    .api-main button { position: absolute; right: 26px; top: 142px; }
    .key-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 86px; border-top: 1px solid #e5e5e5; padding-top: 18px; font-weight: 700; }
    .callout { box-shadow: 0 0 0 4px rgba(244,114,182,.35), 0 0 0 8px rgba(56,189,248,.22) !important; }
    .note-pin {
      position: absolute;
      z-index: 5;
      padding: 9px 12px;
      border-radius: 999px;
      color: #fff;
      background: #e11d48;
      font-weight: 950;
      font-size: 13px;
      box-shadow: 0 10px 24px rgba(225,29,72,.24);
    }
    .note-script { left: 250px; top: 94px; }
    .note-voice { right: 126px; top: 118px; }
    .note-model { right: 56px; top: 220px; }
    .voice-shot { min-height: 420px; background: #fff; }
    .voice-main {
      position: relative;
      margin-left: 170px;
      min-height: 420px;
      padding: 18px 22px 20px;
      background: #fff;
    }
    .voice-breadcrumb { color: #5f6068; font-size: 16px; font-weight: 700; margin-bottom: 20px; }
    .voice-main h3 { margin: 0 0 14px; font-size: 32px; font-weight: 500; }
    .voice-tabs {
      display: flex;
      gap: 18px;
      align-items: center;
      margin-bottom: 14px;
      font-weight: 750;
      color: #777985;
    }
    .voice-tabs span { padding: 9px 11px; border-radius: 11px; }
    .voice-tabs .active { color: #121212; border: 1px solid #d7d7d7; border-bottom: 3px solid #121212; }
    .voice-search {
      height: 42px;
      border: 1px solid #e3e3e8;
      border-radius: 14px;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 14px;
      color: #9798a3;
      font-size: 20px;
      font-weight: 700;
    }
    .voice-search span { color: #222; font-size: 18px; font-weight: 500; }
    .voice-filters { display: flex; gap: 8px; overflow: hidden; margin: 12px 0 18px; white-space: nowrap; }
    .voice-filters span {
      border: 1px solid #e2e2e7;
      border-radius: 12px;
      padding: 9px 12px;
      color: #5f6068;
      font-weight: 750;
      background: #fff;
    }
    .voice-count { margin: 0 0 10px; color: #6a6b73; font-weight: 800; }
    .voice-list { display: grid; gap: 0; border-radius: 16px; overflow: hidden; }
    .voice-row {
      position: relative;
      display: grid;
      grid-template-columns: 40px minmax(180px, 1fr) 92px 82px 72px 118px 34px;
      align-items: center;
      gap: 10px;
      min-height: 58px;
      padding: 6px 10px;
      font-size: 14px;
      color: #242424;
    }
    .voice-row.featured { background: #f0f0f2; }
    .muted-row { color: #4b4c54; }
    .voice-avatar {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: radial-gradient(circle at 30% 30%, #90e0ef, #a78bfa 45%, #475569);
    }
    .voice-avatar.dark { background: radial-gradient(circle at 35% 35%, #fde68a, #7c2d12 50%, #111827); }
    .voice-avatar.blue { background: radial-gradient(circle at 35% 35%, #bae6fd, #64748b 55%, #111827); }
    .voice-title { display: grid; gap: 2px; min-width: 0; }
    .voice-title strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; }
    .voice-title span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #7a7b84; font-weight: 650; }
    .voice-dots {
      width: 30px;
      height: 30px;
      border: 0;
      border-radius: 10px;
      background: #d7d7dd;
      color: #252525;
      font-size: 20px;
      font-weight: 900;
    }
    .voice-menu {
      position: absolute;
      right: 18px;
      top: 232px;
      width: 176px;
      border: 1px solid #dedee4;
      border-radius: 14px;
      background: #fff;
      box-shadow: 0 16px 34px rgba(0,0,0,.18);
      padding: 8px;
      display: grid;
      gap: 2px;
      z-index: 4;
    }
    .voice-menu div {
      padding: 9px 10px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 750;
      color: #1f1f1f;
    }
    .voice-copy-row {
      background: rgba(244,114,182,.08);
      outline: 3px solid rgba(244,114,182,.45);
    }
    .note-voice-id { right: 38px; top: 184px; }
    .note-credit { left: 300px; top: 195px; }
    .note-key { right: 44px; top: 94px; }
    @media (max-width: 920px) {
      .guide-card { grid-template-columns: 1fr; }
      .guide-hero h1 { white-space: normal; }
      .guide-shot { overflow-x: auto; }
    }
""",
    )


UPLOAD_GUIDE_DOCS = {
    "youtube": {
        "path": REPO_ROOT / "docs" / "upload" / "youtube-api-upload.md",
        "kicker": "YouTube API",
        "actions": [
            ("Mở Google Cloud Console", "https://console.cloud.google.com/"),
            ("Docs upload video", "https://developers.google.com/youtube/v3/guides/uploading_a_video"),
            ("Docs OAuth", "https://developers.google.com/youtube/v3/guides/authentication"),
        ],
    },
    "facebook": {
        "path": REPO_ROOT / "docs" / "upload" / "facebook-api-upload.md",
        "kicker": "Facebook Reels API",
        "actions": [
            ("Mở Meta for Developers", "https://developers.facebook.com/"),
            ("Graph API Explorer", "https://developers.facebook.com/tools/explorer/"),
            ("Token Debugger", "https://developers.facebook.com/tools/debug/accesstoken/"),
        ],
    },
}


def markdown_doc_url(target: str, markdown_path: Path) -> str:
    target = str(target or "").strip()
    if re.match(r"^https?://", target):
        return target
    asset_path = (markdown_path.parent / target).resolve()
    try:
        relative = asset_path.relative_to(REPO_ROOT)
    except ValueError:
        return "#"
    return "/" + quote(relative.as_posix(), safe="/._-")


def render_inline_markdown(text: str) -> str:
    rendered = html.escape(text)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)

    def link_repl(match: re.Match) -> str:
        url = match.group(0)
        trailing = ""
        while url and url[-1] in ".,)":
            trailing = url[-1] + trailing
            url = url[:-1]
        escaped_url = html.escape(url, quote=True)
        return f'<a class="text-link" href="{escaped_url}" target="_blank" rel="noreferrer">{html.escape(url)}</a>{trailing}'

    return re.sub(r"https?://[^\s<]+", link_repl, rendered)


def render_markdown_blocks(lines: list[str], markdown_path: Path) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    image_pattern = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            if text:
                blocks.append(f"<p>{render_inline_markdown(text)}</p>")
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            code = html.escape("\n".join(code_lines))
            blocks.append(f"<pre><code>{code}</code></pre>")
            continue

        heading_match = re.match(r"^(#{3,6})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            level = min(len(heading_match.group(1)), 4)
            blocks.append(f"<h{level}>{render_inline_markdown(heading_match.group(2))}</h{level}>")
            index += 1
            continue

        image_match = image_pattern.match(stripped)
        if image_match:
            flush_paragraph()
            images: list[str] = []
            while index < len(lines):
                next_match = image_pattern.match(lines[index].strip())
                if not next_match:
                    break
                alt = next_match.group(1).strip()
                src = markdown_doc_url(next_match.group(2), markdown_path)
                images.append(
                    f'<figure><img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" /></figure>'
                )
                index += 1
            grid_class = "single" if len(images) == 1 else "multi"
            blocks.append(f'<div class="guide-image-grid {grid_class}">' + "".join(images) + "</div>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            items: list[str] = []
            while index < len(lines):
                item_match = re.match(r"^\d+\.\s+(.+)$", lines[index].strip())
                if not item_match:
                    break
                items.append(f"<li>{render_inline_markdown(item_match.group(1))}</li>")
                index += 1
            blocks.append("<ol>" + "".join(items) + "</ol>")
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            items = []
            while index < len(lines):
                item_match = re.match(r"^[-*]\s+(.+)$", lines[index].strip())
                if not item_match:
                    break
                items.append(f"<li>{render_inline_markdown(item_match.group(1))}</li>")
                index += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue

        paragraph.append(line)
        index += 1

    flush_paragraph()
    return "\n".join(blocks)


def split_markdown_guide(markdown_text: str) -> tuple[str, list[str], list[tuple[str, list[str]]]]:
    lines = markdown_text.splitlines()
    title = "Hướng dẫn upload"
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]

    lead: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    section_title = ""
    section_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if section_title or section_lines:
                sections.append((section_title, section_lines))
            section_title = line[3:].strip()
            section_lines = []
            continue
        if section_title:
            section_lines.append(line)
        else:
            lead.append(line)

    if section_title or section_lines:
        sections.append((section_title, section_lines))
    return title, lead, sections


def render_social_upload_guide_html(platform: str) -> bytes:
    platform = platform.strip().lower()
    guide = UPLOAD_GUIDE_DOCS.get(platform)
    if not guide:
        return render_page_shell(
            title="Không tìm thấy hướng dẫn",
            body='<main class="social-guide-page"><a class="small-link back-link" href="/upload">← Quay lại Upload Center</a><h1>Không tìm thấy hướng dẫn upload.</h1></main>',
        )

    markdown_path = guide["path"]
    markdown_text = markdown_path.read_text(encoding="utf-8")
    title, lead_lines, sections = split_markdown_guide(markdown_text)
    lead_html = render_markdown_blocks(lead_lines, markdown_path)
    actions_html = "".join(
        f'<a class="guide-action-link {"small-link" if index else ""}" href="{html.escape(url, quote=True)}" target="_blank" rel="noreferrer">{html.escape(label)}</a>'
        for index, (label, url) in enumerate(guide["actions"])
    )
    section_html = "\n".join(
        f"""
    <section class="md-guide-section">
      <div class="md-section-head">
        <p class="kicker">Guide</p>
        <h2>{render_inline_markdown(section_title)}</h2>
      </div>
      <div class="md-section-body">
        {render_markdown_blocks(section_lines, markdown_path)}
      </div>
    </section>
"""
        for section_title, section_lines in sections
    )

    body = f"""
  <main class="social-guide-page md-guide-page">
    <header class="guide-hero">
      <a class="small-link back-link" href="/upload">← Quay lại Upload Center</a>
      <p class="kicker">{html.escape(str(guide["kicker"]))}</p>
      <h1>{html.escape(title)}</h1>
      <div class="guide-lead">{lead_html}</div>
      <div class="guide-links">{actions_html}</div>
    </header>
    <article class="md-guide">
      {section_html}
    </article>
  </main>
"""

    return render_page_shell(
        title=title,
        body=body,
        extra_style="""
    body { overflow: auto; }
    .social-guide-page {
      width: min(100%, 1280px);
      margin: 0 auto;
    }
    .guide-hero {
      max-width: none;
      margin-bottom: 24px;
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      background: var(--panel);
      box-shadow: var(--shadow);
      padding: clamp(22px, 3vw, 34px);
    }
    .guide-hero h1 {
      max-width: none;
      font-size: clamp(28px, 3vw, 46px);
      line-height: 1;
      white-space: nowrap;
      letter-spacing: -0.03em;
    }
    .guide-lead {
      max-width: 980px;
      color: var(--text-soft);
      font-size: 16px;
      line-height: 1.7;
      font-weight: 400;
    }
    .guide-lead p { margin: 10px 0 0; }
    .back-link { margin-bottom: 18px; }
    .guide-links {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
    }
    .guide-action-link { min-height: 42px; }
    .md-guide {
      display: grid;
      gap: 18px;
    }
    .md-guide-section {
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      padding: clamp(18px, 2.4vw, 28px);
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    .md-section-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 14px;
    }
    .md-section-head .kicker {
      flex: 0 0 auto;
      margin: 0;
    }
    .md-section-head h2 {
      flex: 1 1 auto;
      margin: 0;
      color: var(--text);
      font-size: clamp(24px, 2.35vw, 38px);
      line-height: 1.05;
      letter-spacing: -0.02em;
      text-align: right;
    }
    .md-section-body {
      display: grid;
      gap: 14px;
      color: var(--text-soft);
      font-size: 16px;
      line-height: 1.7;
      font-weight: 400;
    }
    .md-section-body p,
    .md-section-body ol,
    .md-section-body ul { margin: 0; }
    .md-section-body ol,
    .md-section-body ul {
      padding-left: 24px;
    }
    .md-section-body li + li { margin-top: 8px; }
    .md-section-body h3,
    .md-section-body h4 {
      margin: 14px 0 0;
      color: var(--text);
      font-size: clamp(19px, 1.7vw, 26px);
      letter-spacing: -0.02em;
    }
    .md-section-body strong { color: var(--text); font-weight: 600; }
    .md-guide code {
      border-radius: var(--r-sm);
      background: var(--surface-strong);
      color: var(--text);
      padding: 0.05em 0.35em;
      font-weight: 500;
    }
    .md-guide pre {
      margin: 0;
      overflow-x: auto;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      padding: 16px;
      background: var(--surface);
      color: var(--text);
    }
    .md-guide pre code {
      display: block;
      padding: 0;
      background: transparent;
      color: inherit;
      font-family: var(--font-mono);
      font-size: 13px;
      line-height: 1.55;
      white-space: pre;
    }
    .md-guide a.text-link {
      display: inline;
      padding: 0;
      border-radius: 0;
      color: var(--text);
      background: transparent;
      text-decoration: underline;
      text-decoration-thickness: 2px;
      text-underline-offset: 3px;
      font-weight: 600;
    }
    .guide-image-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      align-items: start;
    }
    .guide-image-grid.single { grid-template-columns: minmax(0, 1fr); }
    .guide-image-grid figure {
      margin: 0;
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      padding: 10px;
      background: #fff;
      box-shadow: var(--shadow);
    }
    .guide-image-grid img {
      display: block;
      width: 100%;
      max-height: 640px;
      object-fit: contain;
      border-radius: var(--r-sm);
      background: #fff;
    }
    @media (max-width: 1040px) {
      .guide-hero h1 { white-space: normal; }
      .md-section-head {
        align-items: flex-start;
        flex-direction: column;
      }
      .md-section-head h2 { text-align: left; }
      .guide-image-grid { grid-template-columns: 1fr; }
    }
""",
    )


DASHBOARD_PAGE_STYLE = """
    body {
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      padding: 28px min(4vw, 48px);
    }
    .dashboard-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      width: 100%;
      max-width: 1760px;
      flex: 0 0 auto;
      margin: 0 auto 22px;
    }
    .brand-lockup {
      display: flex;
      align-items: center;
      gap: 18px;
    }
    .brand-mark {
      width: 78px;
      height: 78px;
      border-radius: var(--r-lg);
      object-fit: cover;
      border: 1px solid var(--line);
    }
    .dashboard-header h1 {
      margin: 0;
      font-size: clamp(32px, 4vw, 44px);
      line-height: 1;
      letter-spacing: -0.03em;
    }
    .brand-lockup p {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: clamp(18px, 2.4vw, 26px);
      line-height: 1;
      letter-spacing: -0.03em;
    }
    .kicker { margin: 0 0 6px; color: var(--muted); font-family: var(--font-mono); font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; }
    .header-tools {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      flex: 1 1 auto;
      min-width: 0;
      justify-content: flex-end;
    }
    .guide-header-btn {
      white-space: nowrap;
      padding-inline: 14px;
    }
    .header-stat {
      min-width: 116px;
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      padding: 14px 16px;
      background: var(--surface);
      text-align: center;
    }
    .header-stat strong { display: block; color: var(--text); font-family: var(--font-mono); font-size: 28px; line-height: 1; }
    .header-stat span { color: var(--muted); font-family: var(--font-mono); font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
    .dashboard-shell {
      display: grid;
      grid-template-columns: minmax(360px, 520px) minmax(480px, 1fr);
      gap: 18px;
      width: 100%;
      max-width: 1360px;
      flex: 1 1 auto;
      min-height: 0;
      overflow: hidden;
      margin: 0 auto;
      align-items: stretch;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    .render-machine {
      width: 100%;
      justify-self: stretch;
      align-self: start;
      height: auto;
      max-height: 100%;
      min-height: 0;
      padding: 16px 16px 24px;
      position: static;
      overflow-y: auto;
      overscroll-behavior: contain;
      scroll-padding-bottom: 40px;
      -webkit-overflow-scrolling: touch;
    }
    .slide-list {
      height: 100%;
      min-height: 0;
      padding: 16px;
      overflow-y: auto;
      overscroll-behavior: contain;
      -webkit-overflow-scrolling: touch;
    }
    .panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
    h2 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.02em; }
    .render-heading { text-align: center; margin: 0 0 14px; }
    .render-heading h2 {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 9px;
    }
    .render-heading .kicker { margin-bottom: 3px; }
    .render-lead-icon,
    .tab-icon,
    .field-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      flex: 0 0 auto;
      border-radius: var(--r-sm);
      color: var(--text);
      background: var(--accent-soft);
      font-size: 12px;
      line-height: 1;
      text-shadow: none;
    }
    .render-lead-icon {
      width: 28px;
      height: 28px;
      color: var(--accent-contrast);
      background: var(--accent);
      font-size: 14px;
    }
    .render-machine .field,
    .render-machine .tabs,
    .render-machine .check,
    .render-machine .mode-toggle,
    .render-machine .eleven-actions,
    .render-machine .speed-presets,
    .render-machine .form-actions {
      max-width: 440px;
      margin-left: auto;
      margin-right: auto;
    }
    .field { display: grid; gap: 7px; margin: 10px 0; }
    .field span { color: var(--muted); font-size: 12px; font-weight: 600; }
    .field-label { display: inline-flex; align-items: center; gap: 7px; }
    .mode-toggle {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      margin: 10px auto 12px;
    }
    .mode-toggle label {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      min-height: 38px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      color: var(--text-soft);
      background: var(--surface);
      font-size: 12px;
      font-weight: 600;
    }
    .mode-toggle label:has(input:checked) {
      color: var(--accent-contrast);
      background: var(--accent);
      border-color: var(--accent);
    }
    .eleven-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin: 8px auto 10px;
    }
    .config-state {
      min-width: 0;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      line-height: 1.3;
    }
    .api-key-field { margin-top: 8px; }
    .api-key-panel[hidden] { display: none !important; }
    .api-key-actions {
      align-items: center;
      margin-top: 6px;
      margin-bottom: 14px;
    }
    .save-voice-btn {
      min-height: 36px;
      padding: 8px 12px;
    }
    .engine-note {
      max-width: 440px;
      margin: 10px auto 12px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
      line-height: 1.45;
    }
    .engine-note code {
      color: var(--text);
      font-weight: 600;
    }
    .engine-note.compact {
      margin-top: 8px;
      margin-bottom: 12px;
      padding: 10px 12px;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      background: var(--surface);
    }
    .primary-field { margin-bottom: 12px; }
    .render-primary-actions { margin-top: 12px; }
    .advanced-settings {
      max-width: 440px;
      margin: 14px auto 0;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      background: var(--surface-panel);
      overflow: hidden;
    }
    .advanced-settings summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 48px;
      padding: 10px 12px;
      cursor: pointer;
      list-style: none;
      color: var(--text-soft);
      font-weight: 600;
    }
    .advanced-settings summary::-webkit-details-marker { display: none; }
    .advanced-settings summary::after {
      content: '⌄';
      width: 24px;
      height: 24px;
      border-radius: var(--r-sm);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: var(--accent-contrast);
      background: var(--accent);
      transition: transform 0.18s ease;
      flex: 0 0 auto;
    }
    .advanced-settings[open] summary::after { transform: rotate(180deg); }
    .advanced-summary-main {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }
    .advanced-summary-state {
      margin-left: auto;
      color: var(--muted);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      white-space: nowrap;
    }
    .advanced-body {
      display: grid;
      gap: 0;
      padding: 0 12px 12px;
      border-top: 1px solid var(--control-line-soft);
    }
    .advanced-body .field:first-child { margin-top: 12px; }
    .field input[type="file"] {
      min-height: 54px;
      padding: 8px;
      color: var(--text-soft);
      background: var(--surface);
    }
    body.theme-light .field input[type="file"] {
      background: var(--surface);
    }
    .field input[type="file"]::file-selector-button {
      min-height: 36px;
      margin-right: 12px;
      border: 0;
      border-radius: var(--r-sm);
      padding: 8px 13px;
      color: var(--accent-contrast);
      background: var(--accent);
      font-family: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    .advanced-settings {
      background: var(--surface);
      box-shadow: none;
    }
    .advanced-settings summary {
      min-height: 44px;
      padding: 8px 10px;
      font-size: 15px;
      letter-spacing: -0.02em;
    }
    .advanced-summary-main .btn-icon {
      width: 24px;
      height: 24px;
      font-size: 11px;
    }
    .advanced-summary-state {
      font-size: 10px;
      opacity: 0.62;
      text-transform: none;
      letter-spacing: 0.02em;
    }
    .advanced-settings summary::after {
      width: 22px;
      height: 22px;
      font-size: 12px;
    }
    .advanced-body {
      gap: 4px;
      padding: 12px;
    }
    .advanced-body .field,
    .advanced-body .check,
    .advanced-body .eleven-actions,
    .advanced-body .speed-presets {
      max-width: none;
      margin-left: 0;
      margin-right: 0;
    }
    .advanced-body .field {
      display: grid;
      grid-template-columns: minmax(132px, 0.72fr) minmax(0, 1fr);
      align-items: center;
      gap: 10px 14px;
      margin-top: 0;
      margin-bottom: 0;
    }
    .advanced-body .field:first-child { margin-top: 0; }
    .advanced-body .field-label {
      align-self: center;
      gap: 8px;
      min-width: 0;
    }
    .advanced-body .field-label span:last-child {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .advanced-body .field input,
    .advanced-body .field select {
      min-height: 38px;
      border-radius: var(--r-sm);
    }
    .advanced-body .speed-presets {
      justify-content: center;
      width: 100%;
      margin-top: 5px;
      margin-left: 0;
      margin-bottom: 0;
      gap: 6px;
    }
    .advanced-body .speed-preset {
      min-height: 30px;
      padding: 6px 11px;
      border-radius: var(--r-sm);
    }
    .advanced-body .check {
      min-height: 34px;
      margin-top: 3px;
      margin-bottom: 3px;
      padding: 7px 10px;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-sm);
      background: var(--surface);
      font-size: 12px;
    }
    .advanced-check-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }
    .advanced-body [data-advanced-engine="edgetts"] > .check { margin-top: 5px; }
    .advanced-body .render-speed-block {
      display: grid;
      grid-template-columns: minmax(132px, 0.72fr) minmax(0, 1fr);
      gap: 3px 14px;
      align-items: start;
    }
    .advanced-body .render-speed-field {
      grid-column: 1 / -1;
    }
    .advanced-body .render-options-stack {
      grid-column: 1;
      grid-row: 2;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 3px;
      padding-top: 2px;
    }
    .advanced-body .render-speed-block > .speed-presets {
      grid-column: 2;
      grid-row: 2;
      align-self: start;
    }
    .advanced-body .render-option-row {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 8px;
      margin-top: 0;
      margin-bottom: 0;
    }
    .advanced-body .render-option-check {
      width: auto;
      min-width: 0;
      min-height: 27px;
      justify-content: flex-start;
      gap: 6px;
      margin: 0;
      padding: 4px 8px;
      border-radius: var(--r-sm);
      font-size: 11px;
      line-height: 1.1;
      font-weight: 600;
    }
    .advanced-body .render-option-check input {
      width: 13px;
      height: 13px;
    }
    .render-option-choose,
    .brand-modal-button {
      min-height: 34px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      padding: 7px 13px;
      color: var(--accent-contrast);
      background: var(--accent);
      font: inherit;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
    }
    .render-option-choose:hover,
    .brand-modal-button:hover { transform: translateY(-1px); }
    .render-option-choose {
      min-height: 27px;
      padding: 4px 9px;
      border-radius: var(--r-sm);
      font-size: 10px;
    }
    .brand-modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 220;
      display: grid;
      place-items: center;
      padding: 24px;
      background: rgba(9, 9, 11, 0.5);
    }
    .brand-modal-backdrop[hidden] { display: none !important; }
    .brand-modal-card {
      position: relative;
      width: min(100%, 640px);
      border: 1px solid var(--control-line);
      border-radius: var(--r-lg);
      padding: 22px;
      color: var(--text);
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    .brand-modal-card h3 {
      margin: 0 0 8px;
      font-size: 26px;
      letter-spacing: -0.02em;
    }
    .brand-modal-copy {
      margin: 0 0 16px;
      color: var(--text-faint);
      font-size: 13px;
      line-height: 1.45;
      font-weight: 500;
    }
    .brand-modal-field {
      margin: 10px 0 0 !important;
      padding: 10px 12px;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      background: var(--surface);
    }
    .brand-modal-close {
      position: absolute;
      top: 14px;
      right: 14px;
      width: 34px;
      height: 34px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      color: var(--text);
      background: var(--surface);
      font: inherit;
      font-size: 20px;
      font-weight: 600;
      cursor: pointer;
    }
    .brand-modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 9px;
      margin-top: 16px;
    }
    .brand-modal-button.secondary {
      color: var(--text-button);
      background: var(--surface);
    }
    .advanced-body .eleven-actions {
      justify-content: flex-start;
      flex-wrap: wrap;
      margin-top: 0;
      margin-bottom: 8px;
    }
    .file-picker {
      width: 100%;
      min-height: 54px;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 12px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-md);
      padding: 8px;
      color: var(--text-soft);
      background: var(--surface);
      cursor: pointer;
    }
    body.theme-light .file-picker {
      background: var(--surface);
    }
    .file-picker input[type="file"] {
      position: absolute;
      width: 1px;
      height: 1px;
      opacity: 0;
      pointer-events: none;
    }
    .file-picker-button {
      min-height: 36px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--r-sm);
      padding: 8px 14px;
      color: var(--accent-contrast);
      background: var(--accent);
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .file-picker-name {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--text-soft);
      font-size: 13px;
      font-weight: 500;
    }
    .advanced-settings[open] .advanced-body {
      max-height: none;
      overflow: visible;
      padding-bottom: 20px;
    }
    @media (max-width: 720px) {
      .advanced-check-grid { grid-template-columns: 1fr; }
      .advanced-body .field { grid-template-columns: 1fr; }
      .advanced-body .speed-presets { margin-left: 0; }
      .advanced-body .render-speed-block {
        grid-template-columns: 1fr;
        margin: 0;
      }
      .advanced-body .render-speed-field,
      .advanced-body .render-options-stack,
      .advanced-body .render-speed-block > .speed-presets {
        grid-column: 1;
        grid-row: auto;
      }
      .advanced-body .render-speed-block > .speed-presets { justify-content: flex-start; }
      .advanced-body .render-option-row { display: flex; }
      .brand-modal-actions { flex-direction: column-reverse; }
      .brand-modal-button { width: 100%; }
    }
    .field-label .field-icon {
      font-size: 11px;
    }
    .field input,
    .field select {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      padding: 9px 11px;
      color: var(--text);
      background: var(--field-bg);
    }
    .speed-presets {
      display: flex;
      align-items: center;
      justify-content: center;
      width: fit-content;
      max-width: 100%;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: -2px;
      margin-bottom: 12px;
    }
    .speed-preset {
      min-height: 34px;
      padding: 8px 14px;
      border: 1px solid var(--control-line-faint);
      border-radius: var(--r-sm);
      color: var(--text-soft);
      background: var(--surface);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
    }
    .speed-preset.active {
      color: var(--accent-contrast);
      background: var(--accent);
      border-color: transparent;
    }
    .selected-box {
      max-width: 440px;
      margin: 0 auto;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      padding: 10px 11px;
      background: var(--surface);
      text-align: center;
    }
    .selected-box strong { display: block; margin-bottom: 3px; }
    .selected-box span { display: block; color: var(--muted); font-size: 12px; }
    .form-actions,
    .actions { display: flex; align-items: center; justify-content: flex-end; gap: 6px; flex-wrap: nowrap; white-space: nowrap; }
    .status {
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      padding: 9px 11px;
      background: var(--surface);
      color: var(--status-text);
      font-size: 13px;
      line-height: 1.45;
      margin-top: 10px;
    }
    .render-machine .status {
      max-width: 440px;
      margin: 10px auto 0;
      text-align: center;
    }
    .status.good { border-color: var(--ok); color: var(--good-text); }
    .status.warn { border-color: var(--warn); color: var(--warn-text); }
    .status.bad { border-color: var(--danger); color: var(--danger-text); }
    .cache-warning {
      margin-top: 10px;
      border: 1px solid var(--warn);
      border-radius: var(--r-md);
      padding: 10px 12px;
      color: var(--warning-text);
      background: rgba(217, 119, 6, 0.08);
      font-size: 12px;
      line-height: 1.45;
    }
    .cache-warning strong { display: block; margin-bottom: 6px; color: var(--warn-text); }
    .cache-warning ul { margin: 0; padding-left: 18px; }
    .cache-warning li + li { margin-top: 6px; }
    .header-warning { max-width: 820px; }
    .tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 12px;
      margin-bottom: 12px;
    }
    .tab,
    .select-btn,
    .refresh-btn,
    .delete-output-btn,
    .icon-btn {
      border: 1px solid var(--control-line-faint);
      border-radius: var(--r-sm);
      padding: 8px 10px;
      cursor: pointer;
      color: var(--text-soft);
      background: var(--surface);
      font-weight: 600;
      gap: 6px;
      min-height: 36px;
      font-size: 12px;
      line-height: 1;
      flex: 0 0 auto;
    }
    .tab {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .tab.active .tab-icon,
    .select-btn.active .btn-icon,
    .start .btn-icon {
      color: inherit;
      background: transparent;
      box-shadow: none;
      text-shadow: none;
    }
    .icon-btn { display: inline-flex; align-items: center; justify-content: center; text-decoration: none; }
    .icon-btn[hidden],
    .small-link[hidden] { display: none !important; }
    .btn-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      border-radius: var(--r-sm);
      color: var(--text);
      background: var(--accent-soft);
      font-size: 11px;
      font-weight: 600;
      line-height: 1;
      text-shadow: none;
    }
    .stop-render-btn {
      color: var(--delete-text);
      background: rgba(220, 38, 38, 0.08);
      border-color: rgba(220, 38, 38, 0.35);
    }
    .stop-render-btn .btn-icon,
    .delete-output-btn .btn-icon {
      color: var(--danger);
      background: rgba(220, 38, 38, 0.10);
      text-shadow: none;
    }
    .icon-btn.disabled,
    .icon-btn:disabled {
      opacity: 0.42;
      cursor: not-allowed;
    }
    .icon-btn.disabled {
      pointer-events: none;
    }
    .tab.active,
    .select-btn.active {
      color: var(--accent-contrast);
      background: var(--accent);
      border-color: var(--accent);
    }
    .refresh-btn {
      min-height: 42px;
      color: var(--text);
      background: var(--surface);
      border-color: var(--control-line);
    }
    .delete-output-btn {
      color: var(--delete-text);
      background: rgba(220, 38, 38, 0.08);
      border-color: rgba(220, 38, 38, 0.35);
    }
    .delete-output-btn:hover { background: rgba(220, 38, 38, 0.14); }
    .check { display: flex; align-items: center; gap: 9px; margin: 8px 0 12px; color: var(--status-text); font-size: 13px; }
    .start {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 9px;
      min-height: 42px;
      border: 0;
      border-radius: var(--r-sm);
      padding: 0 18px;
      color: var(--accent-contrast);
      background: var(--accent-strong);
      font-weight: 600;
      cursor: pointer;
    }
    .render-machine .form-actions { justify-content: center; }
    .start:disabled { cursor: wait; opacity: 0.6; }
    .upload-panel {
      max-width: 440px;
      margin: 14px auto 0;
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      padding: 14px;
      background: var(--surface-panel);
    }
    .upload-panel[hidden] { display: none !important; }
    .upload-head { text-align: center; margin-bottom: 10px; }
    .upload-head h3 { margin: 0 0 5px; font-size: 18px; letter-spacing: -0.035em; }
    .upload-head span {
      display: block;
      color: var(--text-faint);
      font-size: 12px;
      line-height: 1.45;
    }
    .upload-field { margin-top: 10px; margin-bottom: 0; }
    .upload-field textarea {
      width: 100%;
      resize: vertical;
      min-height: 104px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      padding: 9px 11px;
      color: var(--text);
      background: var(--field-bg);
      font-family: inherit;
      line-height: 1.45;
    }
    .upload-field.compact { max-width: 240px; }
    .upload-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 12px;
    }
    .upload-btn {
      min-height: 38px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      color: var(--text-button);
      background: var(--surface);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
    }
    .upload-btn:disabled { cursor: not-allowed; opacity: 0.46; }
    .upload-status,
    .upload-result {
      margin-top: 10px;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      padding: 9px 10px;
      color: var(--status-text);
      background: var(--surface);
      font-size: 12px;
      line-height: 1.45;
    }
    .upload-status.good,
    .upload-result.good { border-color: var(--ok); color: var(--good-text); }
    .upload-status.bad,
    .upload-result.bad { border-color: var(--danger); color: var(--danger-text); }
    .upload-status.warn,
    .upload-result.warn { border-color: var(--warn); color: var(--warn-text); }
    .upload-result a { color: var(--accent); font-weight: 600; }
    .render-state {
      width: 100%;
      margin: 14px 0 0;
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      padding: 12px;
      color: var(--text-soft);
      background: var(--surface-panel);
    }
    .state-head {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 9px;
      color: var(--text);
      font-size: 13px;
    }
    .state-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--accent);
    }
    .render-state.running .state-dot {
      animation: statePulse 1s ease-in-out infinite;
    }
    .render-state.failed .state-dot {
      background: var(--danger);
      animation: none;
    }
    .render-state.cancelled .state-dot {
      background: var(--warn);
      animation: none;
    }
    .state-list {
      display: grid;
      gap: 7px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .state-list li {
      display: block;
      overflow: hidden;
      border-radius: var(--r-sm);
      padding: 8px 9px;
      color: var(--text-soft);
      background: var(--surface);
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.45;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .state-list li::before {
      content: none;
    }
    @keyframes statePulse {
      0%, 100% { transform: scale(0.92); opacity: 0.65; }
      50% { transform: scale(1.28); opacity: 1; }
    }
    .list-head,
    .project-row {
      display: grid;
      grid-template-columns: minmax(150px, 1fr) 96px 96px minmax(0, 460px);
      gap: 10px;
      align-items: center;
    }
    .project-row.filtered-out { display: none; }
    .list-head {
      padding: 0 18px 10px;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .list-head span:last-child {
      justify-self: center;
      text-align: center;
    }
    .project-list {
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .project-row {
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      padding: 13px 14px;
      background: var(--surface);
      transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
    }
    .project-row .actions {
      display: grid;
      grid-template-columns: minmax(60px, 82px) minmax(54px, 74px) minmax(62px, 88px) minmax(52px, 70px) minmax(50px, 64px);
      justify-content: end;
      gap: 6px;
      min-width: 0;
      white-space: nowrap;
    }
    .project-row .actions .icon-btn,
    .project-row .actions .select-btn,
    .project-row .actions .small-link,
    .project-row .actions .delete-output-btn {
      width: 100%;
      min-width: 0;
      min-height: 42px;
      padding: 8px 8px;
      border-radius: var(--r-sm);
      font-size: 12px;
    }
    .project-row .actions .btn-icon {
      width: 22px;
      height: 22px;
      flex: 0 0 22px;
    }
    .project-row .row-video-slot {
      min-width: 0;
      width: 100%;
    }
    .project-row.selected {
      border-color: var(--accent);
      background: var(--accent-soft);
      box-shadow: 0 0 0 1px var(--accent);
    }
    .project-main { display: grid; gap: 4px; min-width: 0; }
    .project-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18px; font-weight: 600; letter-spacing: -0.02em; }
    .project-slide-count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: fit-content;
      min-height: 26px;
      white-space: nowrap;
      flex: none;
      padding: 4px 10px;
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-sm);
      color: var(--muted);
      background: var(--surface-strong);
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 500;
    }
    .status-pill {
      justify-self: start;
      border-radius: var(--r-sm);
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .status-pill.ok { color: var(--ok); background: rgba(22, 163, 74, 0.10); border: 1px solid rgba(22, 163, 74, 0.35); }
    .status-pill.bad { color: var(--danger); background: rgba(220, 38, 38, 0.10); border: 1px solid rgba(220, 38, 38, 0.35); }
    .muted, .empty { color: var(--muted); }
    .row-video-slot { display: inline-flex; align-items: center; flex: 0 0 auto; }
    [hidden] { display: none !important; }
    /* Dải trung gian: shell 2 cột nhưng panel danh sách hẹp -> row xếp 2 tầng
       (tên + chi phí tầng 1, trạng thái + thao tác tầng 2) thay vì 4 cột tràn ngang. */
    @media (min-width: 1061px) and (max-width: 1460px) {
      .list-head { display: none; }
      .project-row {
        grid-template-columns: minmax(0, 1fr) auto;
        row-gap: 10px;
      }
      .project-main { grid-column: 1; grid-row: 1; }
      .project-cost { grid-column: 2; grid-row: 1; justify-self: end; text-align: right; }
      .project-row .status-pill { grid-column: 1; grid-row: 2; align-self: center; }
      .project-row .actions { grid-column: 2; grid-row: 2; justify-self: end; }
    }
    @media (max-width: 1060px) {
      body { height: auto; min-height: 100vh; overflow: auto; display: block; }
      .dashboard-header { align-items: flex-start; }
      .dashboard-shell { grid-template-columns: 1fr; min-height: auto; overflow: visible; }
      .render-machine { align-self: auto; height: auto; min-height: 0; position: static; max-height: none; overflow: visible; }
      .slide-list { height: auto; overflow: visible; }
    }
    @media (max-width: 720px) {
      body { padding: 20px 14px; }
      .dashboard-header { display: grid; }
      .header-tools { justify-content: flex-start; }
      .list-head { display: none; }
      .project-row { grid-template-columns: 1fr; align-items: stretch; }
      .project-row .actions {
        grid-template-columns: repeat(5, minmax(0, 1fr));
        justify-content: stretch;
        overflow: visible;
        padding-bottom: 2px;
      }
      .project-row .actions .icon-btn,
      .project-row .actions .select-btn,
      .project-row .actions .small-link,
      .project-row .actions .delete-output-btn {
        padding: 8px 6px;
        font-size: 11px;
      }
    }
    .deck-summary-state { color: var(--muted); font-size: 12px; font-weight: 500; }
    .deck-body { display: flex; flex-direction: column; gap: 12px; }
    .deck-form-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 12px; }
    .deck-form-grid .field { margin: 0; }
    .deck-advanced summary { cursor: pointer; color: var(--muted); font-size: 13px; font-weight: 600; }
    .deck-advanced .field { margin: 10px 0 0; }
    .deck-body textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--r-sm);
      background: transparent;
      color: var(--text);
      font: inherit;
      font-size: 13px;
      padding: 9px 10px;
      resize: vertical;
    }
    .deck-mode-row { display: flex; gap: 18px; flex-wrap: wrap; }
    .deck-mode-option { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; cursor: pointer; }
    .deck-mode-option input { accent-color: var(--accent); }
    .deck-pending { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; font-size: 13px; color: var(--muted); }
    .deck-muted { color: var(--muted); font-size: 12px; font-weight: 400; }
    .deck-drafts { display: flex; flex-direction: column; gap: 10px; }
    .deck-drafts .field { margin: 0; }
    .deck-drafts-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 8px; }
    .deck-draft-card {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      cursor: pointer;
      text-align: left;
      background: transparent;
      color: var(--text);
      font: inherit;
    }
    .deck-draft-card.selected { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }
    .deck-draft-card .draft-style { font-size: 12px; font-weight: 700; color: var(--muted); }
    .deck-draft-card .draft-hook { font-size: 13px; line-height: 1.4; }
    .deck-review { display: flex; flex-direction: column; gap: 10px; border-top: 1px solid var(--line); padding-top: 12px; }
    .deck-review .field { margin: 0; }
    .deck-qa-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; }
    .deck-qa-grid img {
      width: 100%;
      aspect-ratio: 390 / 693;
      object-fit: cover;
      border: 1px solid var(--line);
      border-radius: 8px;
      display: block;
    }
    .deck-result { display: flex; flex-direction: column; gap: 12px; }
    .deck-log summary { cursor: pointer; color: var(--muted); font-size: 12px; font-weight: 600; }
    .deck-log pre {
      max-height: 200px;
      overflow: auto;
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.5;
      white-space: pre-wrap;
      margin: 8px 0 0;
    }
    .project-meta-line { display: inline-flex; align-items: center; gap: 8px; min-width: 0; flex-wrap: wrap; }
    .project-created {
      font-size: 10px;
      color: var(--muted);
      font-family: var(--font-mono);
      white-space: nowrap;
    }
    .project-cost {
      display: grid;
      gap: 2px;
      font-family: var(--font-mono);
      white-space: nowrap;
      min-width: 0;
    }
    .project-cost .cost-usd { font-size: 13px; font-weight: 600; }
    .project-cost .cost-tok { font-size: 10px; color: var(--muted); }
    .project-cost.empty { color: var(--muted); font-size: 12px; }
    .list-toolbar {
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
    }
    .list-toolbar input,
    .list-toolbar select {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      color: var(--text);
      font: inherit;
      font-size: 13px;
      padding: 7px 10px;
    }
    .list-toolbar input { flex: 1; min-width: 0; }
    .list-pager {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin-top: 10px;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 12px;
    }
    .list-pager button:disabled { opacity: 0.4; cursor: default; }
    .deck-cost {
      font-size: 12px;
      color: var(--muted);
      line-height: 1.6;
    }
    .deck-cost strong { color: var(--text); }
    .deck-cost table {
      border-collapse: collapse;
      margin-top: 6px;
      font-size: 11px;
      font-family: var(--font-mono);
    }
    .deck-cost th, .deck-cost td {
      padding: 2px 10px 2px 0;
      text-align: right;
      color: var(--muted);
    }
    .deck-cost th:first-child, .deck-cost td:first-child { text-align: left; }
    .deck-cost th { color: var(--text); font-weight: 600; }
    @media (max-width: 720px) {
      .deck-form-grid { grid-template-columns: 1fr; }
    }
"""


def render_home_html(selected_project: str | None = None) -> bytes:
    projects = list_projects()
    project_names = {project["name"] for project in projects}
    selected_project = selected_project if selected_project in project_names else (projects[0]["name"] if projects else "")

    rows = []
    for project in projects:
        name = html.escape(project["name"])
        href = html.escape(project["url"])
        has_video = bool(project["video_url"])
        can_delete_output = bool(project["has_output"])
        video_link = (
            f'<a class="small-link icon-btn" href="{html.escape(project["video_url"])}" target="_blank" rel="noreferrer"><span class="btn-icon">▶</span><span>Mở</span></a>'
            if has_video
            else '<span class="icon-btn disabled"><span class="btn-icon">▶</span><span>Mở</span></span>'
        )
        delete_disabled = "" if can_delete_output else " disabled"
        delete_disabled_class = "" if can_delete_output else " disabled"
        status = "Sẵn sàng" if project["has_script"] else "Thiếu script"
        status_class = "ok" if project["has_script"] else "bad"
        selected_class = " selected" if project["name"] == selected_project else ""
        cost = project.get("cost")
        if cost:
            tokens = int(cost.get("tokens") or 0)
            if tokens >= 1_000_000:
                tokens_str = f"{tokens / 1_000_000:.1f}M tok"
            elif tokens >= 1_000:
                tokens_str = f"{tokens / 1_000:.0f}k tok"
            else:
                tokens_str = ""
            approx = "" if cost.get("pricing_known") else "+"
            tok_html = f'<span class="cost-tok">{tokens_str}</span>' if tokens_str else ""
            cost_html = f'<div class="project-cost"><span class="cost-usd">≈ ${cost["usd"]:,.2f}{approx}</span>{tok_html}</div>'
        else:
            cost_html = '<div class="project-cost empty">—</div>'
        created_at = float(project.get("created_at") or 0)
        updated_at = float(project.get("updated_at") or 0)
        created_str = time.strftime("%d/%m/%Y", time.localtime(created_at)) if created_at else ""
        created_html = f'<span class="project-created">tạo {created_str}</span>' if created_str else ""
        rows.append(
            f"""
            <li class="project-row{selected_class}" data-project="{name}" data-has-video="{1 if has_video else 0}" data-created="{created_at:.0f}" data-updated="{updated_at:.0f}">
              <div class="project-main">
                <span class="project-name">{name}</span>
                <span class="project-meta-line"><span class="project-slide-count">{project["script_count"] or "?"} slide</span>{created_html}</span>
              </div>
              {cost_html}
              <span class="status-pill {status_class}">{status}</span>
              <div class="actions">
                <button class="select-btn icon-btn" type="button" data-project="{name}"><span class="btn-icon">✓</span><span>Chọn</span></button>
                <a class="small-link icon-btn" href="{href}" target="_blank" rel="noreferrer"><span class="btn-icon">↗</span><span>Xem</span></a>
                <button class="copy-script-btn icon-btn" type="button" data-project="{name}" title="Copy script-90s.txt"><span class="btn-icon">⧉</span><span>Script</span></button>
                <span class="row-video-slot">{video_link}</span>
                <button class="delete-output-btn icon-btn{delete_disabled_class}" type="button" data-project="{name}"{delete_disabled}><span class="btn-icon">×</span><span>Xoá</span></button>
              </div>
            </li>
            """
        )

    body = "\n".join(rows) or '<li class="empty">Chưa có dự án slide nào.</li>'
    return render_page_shell(
        title=f"{branding.BRANDING['name']} Template Web UI",
        body=f"""
  <header class="dashboard-header">
    <div class="brand-lockup">
      <img src="/web/brand-logo" alt="{html.escape(branding.BRANDING['name'])}" class="brand-mark" />
      <div>
        <h1>{html.escape(branding.BRANDING['name'])}</h1>
        <p>Template WebUI</p>
      </div>
    </div>
    <div class="header-tools">
      <a class="refresh-btn icon-btn guide-header-btn" href="/elevenlabs-guide#manual" target="_blank" rel="noreferrer"><span class="btn-icon">?</span><span>Hướng dẫn lấy file audio</span></a>
      <a class="refresh-btn icon-btn guide-header-btn" href="/elevenlabs-guide#api-credit" target="_blank" rel="noreferrer"><span class="btn-icon">?</span><span>Hướng dẫn lấy API + Voice ID</span></a>
      <button class="refresh-btn icon-btn theme-toggle" type="button" data-theme-toggle><span class="btn-icon">☾</span><span>Theme</span></button>
      <button class="refresh-btn icon-btn" type="button" data-source-root-select><span class="btn-icon">⌕</span><span>Source</span></button>
      <a class="refresh-btn icon-btn" href="/create"><span class="btn-icon">＋</span><span>Tạo slide</span></a>
      <a class="refresh-btn icon-btn" href="/upload" target="_blank" rel="noreferrer"><span class="btn-icon">↑</span><span>Upload</span></a>
      <button class="refresh-btn icon-btn" id="refreshProjects" type="button"><span class="btn-icon">↻</span><span>Làm mới</span></button>
      <div class="header-stat"><strong>{len(projects)}</strong><span>dự án</span></div>
    </div>
  </header>

  <main class="dashboard-shell">
    <section class="render-machine panel">
      <div class="render-heading">
        <h2><span class="render-lead-icon">✦</span><span>Bộ máy render</span></h2>
      </div>

      <div class="selected-box">
        <div>
          <strong id="selectedName">Chưa chọn dự án</strong>
        </div>
      </div>

      <div class="status warn" id="renderStatus" hidden></div>

      <div class="tabs">
        <button class="tab active" data-engine="elevenlabs" type="button"><span class="tab-icon">🎙</span><span>ElevenLabs</span></button>
        <button class="tab" data-engine="edgetts" type="button"><span class="tab-icon">⚡</span><span>Edge TTS</span></button>
      </div>

      <div data-pane="elevenlabs">
        <div class="mode-toggle" aria-label="Chọn kiểu ElevenLabs">
          <label><input type="radio" name="elevenMode" value="upload" checked /> Tải file</label>
          <label><input type="radio" name="elevenMode" value="tts" /> API</label>
        </div>
        <div data-eleven-mode-pane="upload">
          <label class="field primary-field">
            <span class="field-label"><span class="field-icon">↑</span><span>File voiceover đầy đủ</span></span>
            <span class="file-picker">
              <input id="elevenFile" type="file" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg" />
              <span class="file-picker-button">Chọn file</span>
              <span class="file-picker-name" id="elevenFileName">Chưa chọn file</span>
            </span>
          </label>
        </div>
        <div data-eleven-mode-pane="tts" hidden>
          <div class="api-key-panel" id="elevenApiKeyPanel">
            <label class="field api-key-field">
              <span class="field-label"><span class="field-icon">🔑</span><span>ElevenLabs API key</span></span>
              <input id="elevenApiKey" type="password" autocomplete="off" placeholder="Dán API key rồi lưu vào config/tts.json" />
            </label>
            <div class="eleven-actions api-key-actions">
              <span class="config-state" id="elevenApiKeyState">Chưa kiểm tra API key</span>
            </div>
          </div>
        </div>
      </div>

      <div data-pane="edgetts" hidden>
      </div>

      <div class="form-actions render-primary-actions">
        <button class="start" id="startRender" type="button" {"disabled" if not projects else ""}><span class="btn-icon">▶</span><span>Bắt đầu render</span></button>
        <button class="icon-btn stop-render-btn" id="stopRender" type="button" hidden><span class="btn-icon">■</span><span>Dừng render</span></button>
        <a class="small-link" id="videoLink" href="#" target="_blank" rel="noreferrer" hidden>Mở video cuối</a>
        <button class="icon-btn reveal-output-btn" id="revealOutput" type="button" hidden><span class="btn-icon">⌕</span><span>Mở trong Finder</span></button>
      </div>

      <div class="render-state" id="renderState" hidden>
        <div class="state-head">
          <span class="state-dot"></span>
          <strong id="stateTitle">Trạng thái render</strong>
        </div>
        <ol class="state-list" id="stateList"></ol>
      </div>
      <div class="deck-cost" id="renderCostLine" hidden></div>

      <details class="advanced-settings" id="advancedSettings">
        <summary>
          <span class="advanced-summary-main"><span class="btn-icon">⚙</span><span>Cài đặt nâng cao</span></span>
          <span class="advanced-summary-state" id="advancedStateLabel">Đang ẩn</span>
        </summary>
        <div class="advanced-body">
          <div data-advanced-engine="elevenlabs">
            <div data-eleven-mode-pane="tts" hidden>
              <label class="field">
                <span class="field-label"><span class="field-icon">♪</span><span>Voice ID, mặc định giọng “Nhật”</span></span>
                <input id="elevenVoice" type="text" placeholder="JBFqnCBsd6RMkjVDRZzb" />
              </label>
              <div class="advanced-check-grid">
                <label class="check">
                  <input id="elevenForce" type="checkbox" />
                  Tạo lại audio cache
                </label>
              </div>
            </div>
          </div>

          <div data-advanced-engine="edgetts" hidden>
            <label class="field">
              <span class="field-label"><span class="field-icon">◆</span><span>Giọng Edge TTS</span></span>
              <input id="edgeVoice" type="text" value="vi-VN-HoaiMyNeural" />
            </label>
            <div class="advanced-check-grid">
              <label class="check">
                <input id="edgeForce" type="checkbox" />
                Tạo lại audio cache
              </label>
            </div>
            <label class="check">
              <input id="edgePerSlide" type="checkbox" />
              Tạo từng slide
            </label>
          </div>

          <div class="render-speed-block">
            <label class="field render-speed-field">
              <span class="field-label"><span class="field-icon">↯</span><span>Tốc độ audio</span></span>
              <input id="renderSpeed" type="number" min="0.5" max="2" step="0.05" value="1.1" />
            </label>
            <div class="render-options-stack">
              <div class="render-option-row">
                <label class="check render-option-check" title="Deck đã có outro slide trong DOM sẽ tự bỏ nối outro.mp4, trừ khi bạn upload file outro riêng.">
                  <input id="renderOutro" type="checkbox" checked />
                  Outro
                </label>
                <button class="render-option-choose" id="chooseOutro" type="button">Chọn</button>
                <input id="outroFile" type="file" accept="video/*,.mp4,.mov,.m4v,.webm" hidden />
              </div>
              <div class="render-option-row">
                <label class="check render-option-check">
                  <input id="renderBranding" type="checkbox" checked />
                  Logo + brand
                </label>
                <button class="render-option-choose" id="openBrandConfig" type="button">Chọn</button>
              </div>
            </div>
            <div class="speed-presets" aria-label="Chọn nhanh tốc độ audio">
              <button class="speed-preset active" type="button" data-speed="1.1">1.1</button>
              <button class="speed-preset" type="button" data-speed="1.15">1.15</button>
              <button class="speed-preset" type="button" data-speed="1.2">1.2</button>
              <button class="speed-preset" type="button" data-speed="1.25">1.25</button>
            </div>
          </div>
          <label class="field render-size-field">
            <span class="field-label"><span class="field-icon">▣</span><span>Độ phân giải render</span></span>
            <select id="renderSize">
              <option value="720x1280" selected>720 x 1280 (mặc định, nhẹ hơn)</option>
              <option value="1080x1920">1080 x 1920 (nét hơn)</option>
            </select>
          </label>
        </div>
      </details>

      <div class="brand-modal-backdrop" id="brandConfigModal" hidden>
        <div class="brand-modal-card" role="dialog" aria-modal="true" aria-labelledby="brandConfigTitle">
          <button class="brand-modal-close" id="closeBrandConfig" type="button" aria-label="Đóng">×</button>
          <p class="kicker">Logo + brand</p>
          <h3 id="brandConfigTitle">Tuỳ chỉnh logo và tên brand</h3>
          <p class="brand-modal-copy">Logo và tên brand chỉ áp dụng khi render, không sửa trực tiếp file slide gốc.</p>
          <label class="field brand-modal-field">
            <span class="field-label"><span class="field-icon">◎</span><span>File logo</span></span>
            <span class="file-picker">
              <input id="brandLogoFile" type="file" accept="image/*,.png,.jpg,.jpeg,.webp,.gif,.ico,.svg" />
              <span class="file-picker-button">Chọn file</span>
              <span class="file-picker-name" id="brandLogoFileName">Chưa chọn logo</span>
            </span>
          </label>
          <label class="field brand-modal-field">
            <span class="field-label"><span class="field-icon">@</span><span>Tên brand</span></span>
            <input id="brandNameInput" type="text" maxlength="64" value="{html.escape(branding.BRANDING['handle'])}" placeholder="{html.escape(branding.BRANDING['handle'])}" />
          </label>
          <div class="brand-modal-actions">
            <button class="brand-modal-button secondary" id="cancelBrandConfig" type="button">Huỷ</button>
            <button class="brand-modal-button" id="saveBrandConfig" type="button">Áp dụng</button>
          </div>
        </div>
      </div>

    </section>

    <aside class="slide-list panel">
      <div class="panel-head">
        <div>
          <p class="kicker">Danh sách</p>
          <h2>Slide trong source folder</h2>
        </div>
      </div>
      <div class="list-toolbar">
        <input type="search" id="projectSearch" placeholder="Lọc theo tên dự án..." autocomplete="off" />
        <select id="projectSort">
          <option value="created_desc">Mới tạo nhất</option>
          <option value="created_asc">Cũ nhất</option>
          <option value="updated_desc">Vừa cập nhật</option>
          <option value="name">Tên A-Z</option>
        </select>
        <select id="projectFilter">
          <option value="all">Tất cả</option>
          <option value="video">Đã render</option>
          <option value="novideo">Chưa render</option>
        </select>
      </div>
      <div class="list-head">
        <span>Dự án</span>
        <span>Chi phí</span>
        <span>Trạng thái</span>
        <span>Thao tác</span>
      </div>
      <ol class="project-list" id="projectList">
        {body}
      </ol>
      <div class="list-pager" id="projectPager" hidden>
        <button class="icon-btn" id="pagerPrev" type="button">‹ Trước</button>
        <span id="pagerInfo"></span>
        <button class="icon-btn" id="pagerNext" type="button">Sau ›</button>
      </div>
    </aside>
  </main>
""",
        extra_style=DASHBOARD_PAGE_STYLE,
        extra_script=f"""
  <script>
    window.__PROJECTS__ = {json.dumps(projects, ensure_ascii=False)};
    window.__INITIAL_PROJECT__ = {json.dumps(selected_project, ensure_ascii=False)};
    window.__PROJECT_SOURCE_ROOT__ = {json.dumps(str(SLIDE_ROOT), ensure_ascii=False)};
  </script>
  <script src="/web/render_page.js?v=20260819-cost-v3"></script>
""",
    )


CREATE_PAGE_EXTRA_STYLE = """
    body {
      height: auto;
      min-height: 100vh;
      overflow: auto;
      display: block;
    }
    .create-shell {
      max-width: 1080px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding-bottom: 60px;
    }
    .deck-step { padding: 18px 20px 20px; }
    .deck-step h2 {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 17px;
      margin: 0 0 14px;
    }
    .deck-step h2 .deck-muted { font-size: 13px; }
    .deck-body { display: flex; flex-direction: column; gap: 12px; padding: 0; max-height: none; overflow: visible; }
    .deck-summary-state { margin-left: auto; }
"""


def render_create_html(deck_allowed: bool = True) -> bytes:
    deck_status = deck_status_payload()
    deck_status["client_allowed"] = bool(deck_allowed)
    deck_enabled = bool(deck_status["available"]) and bool(deck_allowed)
    if not deck_status["available"]:
        deck_hint = deck_unavailable_message(deck_status["reason"])
    elif not deck_allowed:
        deck_hint = "Chỉ tạo được deck từ trình duyệt trên chính máy chạy server (localhost)."
    else:
        deck_hint = ""
    deck_disabled_attr = "" if deck_enabled else " disabled"
    deck_hint_attr = "" if deck_hint else " hidden"
    deck_style_options = "\n".join(
        f'          <option value="{html.escape(item["value"])}">{html.escape(item["label"])}</option>'
        for item in DECK_STYLES
    )
    return render_page_shell(
        title=f"Tạo slide mới — {branding.BRANDING['name']}",
        body=f"""
  <header class="dashboard-header">
    <div class="brand-lockup">
      <img src="/web/brand-logo" alt="{html.escape(branding.BRANDING['name'])}" class="brand-mark" />
      <div>
        <h1>Tạo slide mới</h1>
        <p>Wizard từ link nguồn</p>
      </div>
    </div>
    <div class="header-tools">
      <span class="deck-summary-state" id="deckSummaryState"></span>
      <button class="refresh-btn icon-btn theme-toggle" type="button" data-theme-toggle><span class="btn-icon">☾</span><span>Theme</span></button>
      <a class="refresh-btn icon-btn" href="/"><span class="btn-icon">←</span><span>Bộ máy render</span></a>
    </div>
  </header>

  <main class="create-shell">
    <section class="panel deck-step">
      <h2><span class="btn-icon">🔗</span><span>Nguồn & chế độ</span></h2>
      <div class="deck-body">
        <div class="status warn" id="deckHint"{deck_hint_attr}>{html.escape(deck_hint)}</div>
        <div class="deck-pending" id="deckPending" hidden></div>
        <div class="deck-mode-row">
          <label class="deck-mode-option"><input type="radio" name="deckMode" value="wizard" checked{deck_disabled_attr} /><span>Wizard duyệt từng bước (chọn script, duyệt ảnh)</span></label>
          <label class="deck-mode-option"><input type="radio" name="deckMode" value="auto"{deck_disabled_attr} /><span>Chạy 1 mạch (autopilot)</span></label>
        </div>
        <div class="deck-form-grid">
          <label class="field deck-url-field">
            <span class="field-label"><span class="field-icon">🔗</span><span>Link nguồn (GitHub repo, X post, blog...)</span></span>
            <input id="deckUrl" type="url" placeholder="https://github.com/owner/repo"{deck_disabled_attr} />
          </label>
          <label class="field" id="deckStyleField" hidden>
            <span class="field-label"><span class="field-icon">✎</span><span>Style script</span></span>
            <select id="deckStyle"{deck_disabled_attr}>
{deck_style_options}
            </select>
          </label>
        </div>
        <details class="deck-advanced">
          <summary>Tuỳ chọn thêm</summary>
          <label class="field">
            <span class="field-label"><span>Slug project (bỏ trống để tự đặt theo link)</span></span>
            <input id="deckSlug" type="text" placeholder="owner-repo" pattern="[a-z0-9][a-z0-9-]*"{deck_disabled_attr} />
          </label>
          <label class="field">
            <span class="field-label"><span>Ghi chú thêm cho agent</span></span>
            <textarea id="deckNotes" rows="3" maxlength="2000" placeholder="Ví dụ: tập trung vào benchmark, bỏ qua phần cài đặt..."{deck_disabled_attr}></textarea>
          </label>
        </details>
        <div class="form-actions">
          <button class="start" id="startDeck" type="button"{deck_disabled_attr}><span class="btn-icon">▶</span><span>Bắt đầu</span></button>
          <button class="icon-btn" id="stopDeck" type="button" hidden><span class="btn-icon">■</span><span>Dừng</span></button>
        </div>
        <div class="render-state" id="deckState" hidden>
          <div class="state-head"><span class="state-dot"></span><strong id="deckStateTitle">Trạng thái deck</strong></div>
          <ol class="state-list" id="deckStateList"></ol>
          <details class="deck-log"><summary>Log chi tiết</summary><pre id="deckLogTail"></pre></details>
        </div>
      </div>
    </section>

    <section class="panel deck-step deck-drafts" id="deckDrafts" hidden>
      <h2><span class="btn-icon">✎</span><span>Bước 1/2 — Chọn script</span> <span class="deck-muted">bấm 1 bản để xem, sửa trực tiếp từng dòng ở ô dưới (1 dòng = 1 slide)</span></h2>
      <div class="deck-drafts-list" id="deckDraftsList"></div>
      <label class="field">
        <span class="field-label"><span>Script sẽ dùng</span></span>
        <textarea id="deckDraftLines" rows="8"></textarea>
      </label>
      <div class="form-actions">
        <button class="start" id="confirmDraftBuild" type="button"><span class="btn-icon">▶</span><span>Chốt script & build deck</span></button>
      </div>
    </section>

    <section class="panel deck-step deck-result" id="deckResult" hidden>
      <h2><span class="btn-icon">🖼</span><span>Bước 2/2 — Duyệt ảnh slide</span> <span class="deck-muted">ưng thì Duyệt, chưa ưng thì ghi yêu cầu sửa</span></h2>
      <div class="deck-qa-grid" id="deckQaGrid"></div>
      <div class="deck-review" id="deckReview" hidden>
        <label class="field">
          <span class="field-label"><span>Yêu cầu sửa (ghi rõ slide nào, sửa gì)</span></span>
          <textarea id="deckReviseNotes" rows="3" maxlength="2000" placeholder="Ví dụ: Slide 3 chữ quá nhỏ; slide 5 đổi visual sang dạng timeline..."></textarea>
        </label>
        <div class="form-actions">
          <button class="icon-btn" id="requestRevise" type="button"><span class="btn-icon">✎</span><span>Yêu cầu sửa</span></button>
          <button class="start" id="approveDeck" type="button"><span class="btn-icon">✓</span><span>Duyệt deck</span></button>
        </div>
      </div>
      <div class="form-actions">
        <a class="small-link icon-btn" id="deckOpenLink" href="#" target="_blank" rel="noreferrer"><span class="btn-icon">↗</span><span>Xem deck</span></a>
        <a class="small-link icon-btn" id="deckRenderLink" href="#"><span class="btn-icon">▶</span><span>Mở màn hình render</span></a>
      </div>
      <div class="status warn" id="deckWarnings" hidden></div>
      <div class="deck-cost" id="deckCostSummary" hidden></div>
    </section>
  </main>
""",
        extra_style=DASHBOARD_PAGE_STYLE + CREATE_PAGE_EXTRA_STYLE,
        extra_script=f"""
  <script>
    window.__PROJECTS__ = [];
    window.__DECK__ = {json.dumps(deck_status, ensure_ascii=False)};
  </script>
  <script src="/web/render_page.js?v=20260819-cost-v3"></script>
""",
    )


def render_upload_html(selected_project: str | None = None) -> bytes:
    projects = list_projects()
    project_names = {project["name"] for project in projects}
    output_projects = [project for project in projects if project["video_url"]]
    if selected_project not in project_names:
        selected_project = output_projects[0]["name"] if output_projects else (projects[0]["name"] if projects else "")

    options = "\n".join(
        f'<option value="{html.escape(project["name"])}" {"selected" if project["name"] == selected_project else ""}>'
        f'{html.escape(project["name"])}'
        "</option>"
        for project in projects
    )
    return render_page_shell(
        title=f"{branding.BRANDING['name']} Upload Center",
        body=f"""
  <main class="upload-shell">
    <section class="upload-machine">
      <div class="top-upload-bar">
        <div class="top-project-row">
          <img src="/web/brand-logo" alt="{html.escape(branding.BRANDING['name'])}" class="upload-brand-mark" />
          <label class="field project-select-field field-project top-project-field">
          <span class="project-field-head">
            <span class="field-label"><span class="field-icon">P</span><span>Project</span></span>
            <span class="project-video-badge" id="projectVideoBadge">final_video</span>
          </span>
            <select id="projectSelect" {"disabled" if not projects else ""}>
              {options}
            </select>
          </label>
        </div>
        <div class="top-upload-actions">
          <span class="ready-pill"><strong>{len(output_projects)}</strong><span>sẵn sàng</span></span>
          <div class="header-tools">
            <button class="refresh-btn icon-btn theme-toggle" type="button" data-theme-toggle><span class="btn-icon">☾</span><span>Theme</span></button>
            <button class="refresh-btn icon-btn" type="button" data-source-root-select><span class="btn-icon">⌕</span><span>Source</span></button>
            <a class="refresh-btn icon-btn" href="/"><span class="btn-icon">←</span><span>Dashboard</span></a>
            <button class="refresh-btn icon-btn" id="refreshProjects" type="button"><span class="btn-icon">↻</span><span>Làm mới</span></button>
          </div>
        </div>
      </div>

      <div class="status warn" id="renderStatus" hidden></div>

      <div class="upload-empty" id="uploadEmpty" hidden>
        <strong id="uploadEmptyProject">Project này chưa có final_video.mp4</strong>
        <span>Render project ở Dashboard trước, rồi quay lại Upload Center để đăng.</span>
        <a class="small-link" href="/">Về Dashboard</a>
      </div>

      <div class="upload-panel" id="uploadPanel" hidden>
        <div class="platform-grid">
          <section class="platform-card platform-youtube">
            <div class="platform-card-head">
              <div class="platform-title"><span class="field-icon">YT</span><span>YouTube</span></div>
              <a class="small-link icon-btn platform-guide-link" href="/upload-guide/youtube" target="_blank" rel="noreferrer"><span class="btn-icon">?</span><span>Hướng dẫn YouTube</span></a>
            </div>
            <div class="platform-account-list" id="youtubeAccountList" hidden></div>
            <div class="field upload-field field-title">
              <span class="field-label field-label-between">
                <span class="field-label-main"><span class="field-icon">T</span><span>YouTube Title</span></span>
                <button class="copy-field-btn" data-copy-target="uploadTitle" data-copy-label="YouTube Title" type="button" aria-label="Copy YouTube Title" title="Copy YouTube Title"><span class="btn-icon">⧉</span></button>
              </span>
              <input id="uploadTitle" type="text" maxlength="100" placeholder="Tiêu đề YouTube" />
            </div>
            <div class="field upload-field field-description">
              <span class="field-label field-label-between">
                <span class="field-label-main"><span class="field-icon">≡</span><span>YouTube Description</span></span>
                <button class="copy-field-btn" data-copy-target="youtubeDescription" data-copy-label="YouTube Description" type="button" aria-label="Copy YouTube Description" title="Copy YouTube Description"><span class="btn-icon">⧉</span></button>
              </span>
              <textarea id="youtubeDescription" rows="7" maxlength="5000" placeholder="Mô tả YouTube, có nguồn và hashtag"></textarea>
            </div>
            <label class="field upload-field compact field-youtube">
              <span class="field-label"><span>YouTube visibility</span></span>
              <select id="youtubePrivacy">
                <option value="private">Private - duyệt trước</option>
                <option value="unlisted">Unlisted - có link mới xem</option>
                <option value="public" selected>Public - đăng công khai</option>
              </select>
            </label>
            <div class="platform-actions">
              <button class="upload-btn youtube" id="connectYoutube" type="button"><span class="btn-icon">▶</span><span>Connect</span></button>
              <button class="upload-btn youtube" id="uploadYoutube" type="button"><span class="btn-icon">↑</span><span>Upload YouTube</span></button>
            </div>
          </section>
          <section class="platform-card platform-facebook">
            <div class="platform-card-head">
              <div class="platform-title"><span class="field-icon">f</span><span>Facebook Reels</span></div>
              <a class="small-link icon-btn platform-guide-link" href="/upload-guide/facebook" target="_blank" rel="noreferrer"><span class="btn-icon">?</span><span>Hướng dẫn Facebook</span></a>
            </div>
            <div class="platform-account-list" id="facebookAccountList" hidden></div>
            <div class="field upload-field field-description">
              <span class="field-label field-label-between">
                <span class="field-label-main"><span class="field-icon">≡</span><span>Facebook Caption</span></span>
                <button class="copy-field-btn" data-copy-target="facebookCaption" data-copy-label="Facebook Caption" type="button" aria-label="Copy Facebook Caption" title="Copy Facebook Caption"><span class="btn-icon">⧉</span></button>
              </span>
              <textarea id="facebookCaption" rows="7" maxlength="5000" placeholder="Caption Reels, không chứa link nguồn"></textarea>
            </div>
            <div class="field upload-field field-source-comment">
              <span class="field-label field-label-between">
                <span class="field-label-main"><span class="field-icon">↳</span><span>Source comment</span></span>
                <button class="copy-field-btn" data-copy-target="facebookSourceComment" data-copy-label="Source comment" type="button" aria-label="Copy Source comment" title="Copy Source comment"><span class="btn-icon">⧉</span></button>
              </span>
              <input id="facebookSourceComment" type="text" maxlength="1000" placeholder="Nguồn: https://..." />
            </div>
            <label class="field upload-field compact field-facebook">
              <span class="field-label"><span>Reels status</span></span>
              <select id="facebookVideoState">
                <option value="DRAFT">Draft - duyệt trước</option>
                <option value="PUBLISHED" selected>Publish now</option>
              </select>
            </label>
            <div class="platform-actions">
              <button class="upload-btn facebook secondary" id="openFacebookConfig" type="button"><span class="btn-icon">+</span><span>Thêm Page</span></button>
              <button class="upload-btn facebook" id="uploadFacebook" type="button"><span class="btn-icon">f</span><span>Upload Facebook Reels</span></button>
            </div>
          </section>
        </div>
        <div class="final-upload-actions">
          <button class="upload-btn both" id="uploadBothPublic" type="button" disabled><span class="btn-icon">✓</span><span>Upload Facebook + YouTube + comment nguồn</span></button>
        </div>
        <div class="upload-status" id="uploadStatus" hidden></div>
        <div class="upload-result" id="uploadResult" hidden></div>
      </div>
      <div class="modal-backdrop" id="facebookConfigModal" hidden>
        <div class="modal-card facebook-config-modal" role="dialog" aria-modal="true" aria-labelledby="facebookConfigTitle">
          <button class="modal-close" id="closeFacebookConfig" type="button" aria-label="Đóng">×</button>
          <p class="kicker">Facebook Page</p>
          <h3 id="facebookConfigTitle">Thêm Page</h3>
          <p class="modal-copy">Dán Page ID và Page access token đã extend. Token sẽ được lưu vào <code>config/social-upload.json</code> và không hiện lại trên UI.</p>
          <div class="field upload-field compact facebook-config-field">
            <span class="field-label"><span class="field-icon">ID</span><span>Facebook Page ID</span></span>
            <input id="facebookPageId" type="text" inputmode="numeric" autocomplete="off" placeholder="Dán Page ID" />
          </div>
          <div class="field upload-field compact facebook-config-field">
            <span class="field-label"><span class="field-icon">🔑</span><span>Page access token</span></span>
            <input id="facebookPageAccessToken" type="password" autocomplete="off" placeholder="Dán Page access token" />
          </div>
          <div class="modal-actions">
            <button class="upload-btn secondary" id="cancelFacebookConfig" type="button"><span class="btn-icon">×</span><span>Huỷ</span></button>
            <button class="upload-btn facebook" id="saveFacebookConfig" type="button"><span class="btn-icon">✓</span><span>Lưu Page</span></button>
          </div>
        </div>
      </div>
    </section>
  </main>
""",
        extra_style="""
    body {
      --upload-page-max: 1800px;
      padding: 24px clamp(24px, 3vw, 56px);
    }
    .upload-header {
      display: grid;
      grid-template-columns: minmax(320px, 0.86fr) minmax(420px, 1fr);
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      width: min(100%, var(--upload-page-max));
      max-width: var(--upload-page-max);
      margin: 0 auto 22px;
    }
    .upload-title-block {
      display: flex;
      align-items: center;
      gap: 14px;
      min-height: 74px;
    }
    .upload-brand-mark {
      width: 58px;
      height: 58px;
      flex: 0 0 58px;
      border-radius: var(--r-md);
      object-fit: cover;
      border: 1px solid var(--line);
    }
    .upload-header h1 {
      margin: 0;
      font-size: clamp(36px, 4.4vw, 54px);
      line-height: 0.95;
      letter-spacing: -0.03em;
      white-space: nowrap;
    }
    .kicker { margin: 0 0 6px; color: var(--muted); font-family: var(--font-mono); font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; }
    .header-tools {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      justify-content: end;
      align-items: stretch;
      width: min(100%, 520px);
      justify-self: end;
    }
    .upload-header .refresh-btn {
      min-height: 42px;
      padding: 8px 12px;
      width: 100%;
      white-space: nowrap;
    }
    .upload-shell {
      width: min(100%, var(--upload-page-max));
      max-width: var(--upload-page-max);
      margin: 0 auto;
    }
    .upload-machine { display: grid; gap: 10px; }
    .top-upload-bar {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 14px;
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      padding: 10px 12px;
      background: var(--surface-panel);
      box-shadow: var(--shadow);
    }
    .top-project-row {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .top-upload-bar .upload-brand-mark {
      width: 44px;
      height: 44px;
      flex: 0 0 44px;
      border-radius: var(--r-md);
    }
    .top-project-field {
      display: grid;
      grid-template-columns: auto minmax(260px, 1fr);
      align-items: center;
      gap: 10px;
      width: 100%;
      min-width: 0;
    }
    .top-project-field .project-field-head {
      justify-content: flex-start;
      flex-wrap: nowrap;
      min-width: 0;
    }
    .top-project-field select {
      min-height: 42px;
      padding-block: 8px;
      font-size: 14px;
    }
    .top-upload-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      min-width: 0;
    }
    .top-upload-actions .ready-pill {
      min-height: 40px;
      padding: 7px 11px;
    }
    .top-upload-actions .header-tools {
      width: auto;
      grid-template-columns: repeat(4, minmax(96px, auto));
    }
    .top-upload-actions .refresh-btn {
      min-height: 40px;
      padding: 8px 11px;
    }
    .project-picker {
      display: grid;
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      padding: 14px;
      background: var(--surface-panel);
      box-shadow: var(--shadow);
    }
    .project-picker-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
    }
    h2 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.02em; }
    .ready-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--accent);
      border-radius: var(--r-sm);
      padding: 7px 11px;
      color: var(--accent-contrast);
      background: var(--accent);
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .ready-pill strong { font-size: 16px; line-height: 1; }
    .ready-pill span { text-transform: uppercase; letter-spacing: 0.08em; }
    .field-project,
    .project-summary,
    .field-title,
    .field-description,
    .field-youtube,
    .field-facebook,
    .field-source-comment,
    .platform-youtube,
    .platform-facebook {
      --field-accent: var(--accent);
      --field-accent-2: var(--muted);
      --field-tint: var(--accent-soft);
      --field-border: var(--control-line);
      --field-icon-text: var(--accent-contrast);
    }
    .field-source-comment {
      max-width: 520px;
    }
    .field { display: grid; gap: 7px; margin: 0; }
    .field > span { color: var(--muted); font-size: 12px; font-weight: 600; }
    .field-label,
    .summary-label {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      justify-self: start;
      color: var(--field-accent-2, var(--muted));
    }
    .field-label-between {
      width: 100%;
      justify-content: space-between;
      gap: 12px;
    }
    .field-label-main {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }
    .project-field-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    .project-video-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--r-sm);
      padding: 7px 11px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .project-video-badge.ready {
      color: var(--ok);
      border: 1px solid rgba(22, 163, 74, 0.35);
      background: rgba(22, 163, 74, 0.10);
    }
    .project-video-badge.missing {
      color: var(--warn);
      border: 1px solid rgba(217, 119, 6, 0.35);
      background: rgba(217, 119, 6, 0.10);
    }
    .field-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: var(--r-sm);
      color: var(--text);
      background: var(--accent-soft);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: -0.03em;
      line-height: 1;
    }
    .field input,
    .field select,
    .field textarea {
      width: 100%;
      min-height: 46px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      padding: 11px 13px;
      color: var(--text);
      background: var(--field-bg);
      font-family: inherit;
      line-height: 1.45;
    }
    .field input:focus,
    .field select:focus,
    .field textarea:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }
    .platform-card .upload-field.compact.field-youtube,
    .platform-card .upload-field.compact.field-facebook {
      width: min(100%, 260px);
      max-width: 260px;
    }
    .project-select-field select {
      min-height: 48px;
      border-color: var(--control-line);
      border-radius: var(--r-sm);
      background: var(--field-bg);
      font-size: 15px;
      font-weight: 600;
    }
    .field textarea { resize: vertical; min-height: 150px; }
    .field-source-comment input {
      min-height: 44px;
      padding-block: 9px;
      font-size: 14px;
    }
    .copy-field-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 0 0 auto;
      width: 32px;
      height: 32px;
      border: 1px solid var(--field-border);
      border-radius: var(--r-sm);
      padding: 0;
      color: var(--text-soft);
      background: var(--surface);
      font: inherit;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.02em;
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
      white-space: nowrap;
    }
    .copy-field-btn:hover {
      transform: translateY(-1px);
      border-color: color-mix(in srgb, var(--field-accent) 72%, white 28%);
      box-shadow: 0 10px 24px color-mix(in srgb, var(--field-accent) 20%, transparent);
    }
    .copy-field-btn:focus-visible {
      outline: none;
      box-shadow:
        0 0 0 3px color-mix(in srgb, var(--field-accent) 22%, transparent),
        0 10px 24px color-mix(in srgb, var(--field-accent) 18%, transparent);
    }
    .copy-field-btn .btn-icon {
      font-size: 14px;
      line-height: 1;
    }
    .project-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 0;
    }
    .project-summary > div { min-width: 0; }
    .summary-label {
      display: inline-flex;
      margin-bottom: 7px;
      color: var(--field-accent-2);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .project-summary strong {
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-bottom: 3px;
      font-size: 20px;
      letter-spacing: -0.02em;
    }
    .quick-links { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 2px; }
    .status,
    .upload-empty,
    .upload-status,
    .upload-result {
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      padding: 10px 11px;
      color: var(--status-text);
      background: var(--surface);
      font-size: 13px;
      line-height: 1.45;
    }
    .status.good,
    .upload-status.good,
    .upload-result.good { border-color: var(--ok); color: var(--good-text); }
    .status.bad,
    .upload-status.bad,
    .upload-result.bad { border-color: var(--danger); color: var(--danger-text); }
    .status.warn,
    .upload-status.warn,
    .upload-result.warn { border-color: var(--warn); color: var(--warn-text); }
    .upload-empty { display: grid; gap: 8px; }
    .upload-empty strong { color: var(--warn-text); }
    .upload-panel {
      border: 1px solid var(--line);
      border-radius: var(--r-lg);
      padding: 14px;
      background: var(--surface-panel);
      box-shadow: var(--shadow);
    }
    .upload-head { text-align: center; margin-bottom: 8px; }
    .upload-head h3 { margin: 0 0 5px; font-size: 20px; letter-spacing: -0.035em; }
    .upload-head span { display: block; color: var(--text-faint); font-size: 12px; line-height: 1.45; }
    .upload-field { margin-top: 8px; }
    .upload-field.compact { max-width: none; }
    .platform-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: clamp(12px, 1.4vw, 22px);
      margin-top: 0;
      align-items: stretch;
    }
    .platform-card {
      border: 1px solid var(--field-border);
      border-radius: var(--r-md);
      padding: 12px;
      background: var(--surface);
    }
    .platform-youtube { order: 2; }
    .platform-facebook { order: 1; }
    .platform-card-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .platform-title {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--field-accent-2);
      font-size: 13px;
      font-weight: 600;
      letter-spacing: -0.02em;
    }
    .platform-guide-link {
      min-height: 34px;
      padding: 7px 10px;
      flex: 0 0 auto;
      border-color: var(--field-border);
      font-size: 11px;
    }
    .platform-account-list {
      display: grid;
      gap: 8px;
      margin-top: 10px;
      position: relative;
      z-index: 3;
    }
    .platform-account-list.open {
      z-index: 80;
    }
    .platform-account {
      display: grid;
      grid-template-columns: 42px minmax(0, 1fr);
      align-items: center;
      gap: 10px;
      width: 100%;
      border: 1px solid var(--field-border);
      border-radius: var(--r-md);
      padding: 9px;
      background: var(--surface);
      color: inherit;
      font: inherit;
      text-align: left;
    }
    button.platform-account {
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
    }
    button.platform-account:hover:not(:disabled) {
      transform: translateY(-1px);
      border-color: var(--muted);
    }
    button.platform-account:disabled {
      cursor: default;
      opacity: 0.78;
    }
    .platform-account.active {
      border-color: var(--accent);
      background: var(--accent-soft);
      box-shadow: inset 0 0 0 1px var(--accent);
    }
    .platform-account-trigger {
      grid-template-columns: 42px minmax(0, 1fr) auto;
    }
    .account-chevron {
      display: inline-flex !important;
      align-items: center;
      justify-content: center;
      min-width: auto !important;
      overflow: visible !important;
      color: var(--text-faint);
      font-size: 18px;
      font-weight: 600;
      line-height: 1;
      transition: transform 0.16s ease;
    }
    .platform-account-list.open .account-chevron {
      transform: rotate(180deg);
    }
    .platform-account-options {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      right: 0;
      display: none;
      gap: 7px;
      z-index: 20;
      border: 1px solid var(--control-line);
      border-radius: var(--r-md);
      padding: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    .platform-account-list.open .platform-account-options {
      display: grid;
    }
    .platform-account-option {
      border-color: var(--control-line-soft);
      background: var(--surface);
    }
    .platform-account img {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      object-fit: cover;
      background: var(--surface-strong);
    }
    .platform-account strong,
    .platform-account span {
      display: block;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .platform-account strong {
      color: var(--text);
      font-size: 13px;
      font-weight: 600;
    }
    .platform-account span {
      margin-top: 3px;
      color: var(--text-faint);
      font-size: 11px;
      font-weight: 500;
    }
    .platform-card .upload-field {
      margin-top: 10px;
      padding: 0;
      border: 0;
      background: transparent;
    }
    .platform-card .field-source-comment {
      max-width: 520px;
    }
    .platform-card .field-source-comment input {
      min-height: 44px;
      padding-block: 9px;
      font-size: 14px;
    }
    .facebook-config-field {
      display: grid;
      grid-template-columns: minmax(120px, 0.64fr) minmax(0, 1fr);
      align-items: center;
      gap: 9px;
      margin: 0 !important;
    }
    .facebook-config-field input {
      min-height: 42px;
      font-size: 13px;
    }
    .config-actions {
      align-items: center;
      margin-top: 0;
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 200;
      display: grid;
      place-items: center;
      padding: 24px;
      background: rgba(9, 9, 11, 0.5);
    }
    .modal-card {
      position: relative;
      width: min(100%, 560px);
      border: 1px solid var(--control-line);
      border-radius: var(--r-lg);
      padding: 22px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    .facebook-config-modal {
      width: min(100%, 720px);
    }
    .modal-card h3 {
      margin: 0 0 8px;
      font-size: 30px;
      letter-spacing: -0.02em;
    }
    .facebook-config-modal .kicker,
    .facebook-config-modal h3,
    .facebook-config-modal .field-label,
    .facebook-config-modal .field-label span {
      color: currentColor;
    }
    .modal-copy {
      margin: 0 0 16px;
      color: var(--text-faint);
      font-size: 13px;
      line-height: 1.45;
      font-weight: 500;
    }
    .facebook-config-modal .modal-copy {
      max-width: 610px;
      color: var(--text-faint);
      font-size: 14px;
      font-weight: 500;
    }
    .modal-copy code {
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 12px;
    }
    .facebook-config-modal .modal-copy code {
      color: var(--text);
      background: var(--surface-strong);
      border-radius: var(--r-sm);
      padding: 2px 5px;
      font-weight: 600;
    }
    .facebook-config-modal .facebook-config-field {
      border: 1px solid var(--control-line-soft);
      border-radius: var(--r-md);
      padding: 10px 12px;
      background: var(--surface);
    }
    .facebook-config-modal .facebook-config-field + .facebook-config-field {
      margin-top: 10px !important;
    }
    .facebook-config-modal .facebook-config-field input {
      color: var(--text);
      border-color: var(--control-line);
      background: var(--field-bg);
    }
    .facebook-config-modal .facebook-config-field input::placeholder {
      color: var(--text-faint);
    }
    .modal-close {
      position: absolute;
      top: 14px;
      right: 14px;
      width: 34px;
      height: 34px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      color: var(--text);
      background: var(--surface);
      font: inherit;
      font-size: 20px;
      font-weight: 600;
      cursor: pointer;
    }
    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 9px;
      margin-top: 16px;
    }
    body:not(.theme-light) .upload-panel .platform-card .upload-field {
      padding: 0;
      border: 0;
      background: transparent;
    }
    .platform-actions {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .final-upload-actions {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 9px;
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid var(--control-line-soft);
    }
    .upload-btn,
    .refresh-btn,
    .icon-btn {
      min-height: 40px;
      border: 1px solid var(--control-line);
      border-radius: var(--r-sm);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      color: var(--text-button);
      background: var(--surface);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
    }
    .platform-actions .upload-btn {
      width: auto;
      min-height: 38px;
      padding: 8px 12px;
      flex: 0 0 auto;
      justify-content: center;
    }
    .refresh-btn {
      color: var(--text);
      background: var(--surface);
      border-color: var(--control-line);
    }
    .upload-btn.both {
      min-width: min(100%, 360px);
      min-height: 44px;
      padding: 10px 18px;
      border-color: var(--accent);
      background: var(--accent);
      color: var(--accent-contrast);
    }
    .upload-btn:disabled { cursor: not-allowed; opacity: 0.46; }
    .btn-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      border-radius: var(--r-sm);
      color: var(--text);
      background: var(--accent-soft);
      font-size: 11px;
      font-weight: 600;
      line-height: 1;
      text-shadow: none;
    }
    .upload-btn.both .btn-icon {
      color: inherit;
      background: transparent;
    }
    .upload-status {
      width: fit-content;
      max-width: min(100%, 860px);
      margin: 14px auto 0;
    }
    .upload-result { margin-top: 10px; }
    .small-link { color: var(--text); background: var(--surface-strong); }
    .upload-result a { color: var(--accent); font-weight: 600; background: transparent; padding: 0; }
    [hidden] { display: none !important; }
    @media (max-width: 980px) {
      .upload-header { display: grid; }
      .header-tools { justify-content: stretch; justify-self: stretch; width: 100%; }
    }
    @media (max-width: 720px) {
      body { padding: 20px 14px; }
      .project-picker-head,
      .project-summary { align-items: flex-start; flex-direction: column; }
      .upload-header { grid-template-columns: 1fr; gap: 16px; }
      .upload-title-block { min-height: 0; }
      .header-tools { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .platform-card-head { align-items: flex-start; flex-direction: column; }
      .platform-grid { grid-template-columns: 1fr; }
      .facebook-config-field { grid-template-columns: 1fr; }
      .modal-actions { flex-direction: column-reverse; }
      .modal-actions .upload-btn { width: 100%; }
    }
""",
        extra_script=f"""
  <script>
    window.__PROJECTS__ = {json.dumps(projects, ensure_ascii=False)};
    window.__INITIAL_PROJECT__ = {json.dumps(selected_project, ensure_ascii=False)};
    window.__PROJECT_SOURCE_ROOT__ = {json.dumps(str(SLIDE_ROOT), ensure_ascii=False)};
  </script>
  <script src="/web/render_page.js?v=20260819-cost-v3"></script>
""",
    )


def render_page_shell(title: str, body: str, extra_style: str = "", extra_script: str = "") -> bytes:
    html_text = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <link rel="icon" href="/web/favicon.ico" sizes="any" />
  <link rel="shortcut icon" href="/web/favicon.ico" type="image/x-icon" />
  <script>window.__BRANDING__ = {BRANDING_CLIENT_JSON};</script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    /* NiceSoft Design System v1.2.1 "Mono" — brand: soft (house).
       NiceTechChannels chưa có token riêng nên dùng nguyên token house:
       grayscale lo hierarchy, accent = ink (dark: paper). */
    :root {{
      color-scheme: dark;
      --bg: #09090B;
      --panel: #111113;
      --line: rgba(255, 255, 255, 0.10);
      --text: #FAFAFA;
      --muted: #A1A1AA;
      --accent: #FAFAFA;
      --accent-strong: #FFFFFF;
      --accent-soft: rgba(255, 255, 255, 0.10);
      --accent-contrast: #09090B;
      --body-bg: var(--bg);
      --surface: #111113;
      --surface-strong: #18181B;
      --surface-panel: #111113;
      --field-bg: #09090B;
      --control-line: rgba(255, 255, 255, 0.16);
      --control-line-soft: rgba(255, 255, 255, 0.10);
      --control-line-faint: rgba(255, 255, 255, 0.10);
      --text-soft: #D4D4D8;
      --text-faint: #A1A1AA;
      --text-button: #FAFAFA;
      --status-text: #A1A1AA;
      --ok: #16A34A;
      --warn: #D97706;
      --danger: #DC2626;
      --good-text: var(--ok);
      --warn-text: var(--warn);
      --danger-text: var(--danger);
      --delete-text: var(--danger);
      --warning-text: var(--warn);
      --shadow: none;
      --accent-glow: transparent;
      --r-sm: 6px;
      --r-md: 10px;
      --r-lg: 14px;
      --font-ui: "Geist", "Inter", ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;
    }}
    body.theme-light {{
      color-scheme: light;
      --bg: #FFFFFF;
      --panel: #FFFFFF;
      --line: #E4E4E7;
      --text: #09090B;
      --muted: #71717A;
      --accent: #18181B;
      --accent-strong: #09090B;
      --accent-soft: rgba(9, 9, 11, 0.06);
      --accent-contrast: #FFFFFF;
      --body-bg: var(--bg);
      --surface: #FAFAFA;
      --surface-strong: #F4F4F5;
      --surface-panel: #FAFAFA;
      --field-bg: #FFFFFF;
      --control-line: #D4D4D8;
      --control-line-soft: #E4E4E7;
      --control-line-faint: #E4E4E7;
      --text-soft: #3F3F46;
      --text-faint: #71717A;
      --text-button: #18181B;
      --status-text: #71717A;
      --good-text: var(--ok);
      --warn-text: var(--warn);
      --danger-text: var(--danger);
      --delete-text: var(--danger);
      --warning-text: var(--warn);
      --shadow: 0 4px 16px rgba(9, 9, 11, 0.08);
      --accent-glow: transparent;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: var(--font-ui);
      font-feature-settings: "ss01" 1, "cv01" 1;
      color: var(--text);
      background: var(--body-bg);
      accent-color: var(--accent);
      padding: 44px min(5vw, 72px);
    }}
    header {{ max-width: 920px; margin-bottom: 34px; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(36px, 6vw, 76px); line-height: 0.98; letter-spacing: -0.03em; }}
    header p {{ max-width: 720px; color: var(--muted); font-size: 17px; line-height: 1.6; }}
    code {{ font-family: var(--font-mono); color: var(--text); }}
    a {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--r-sm);
      padding: 10px 14px;
      color: var(--accent-contrast);
      background: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
    .small-link {{ color: var(--text); background: var(--surface-strong); }}
{extra_style}
  </style>
</head>
<body class="theme-light">
{body}
{extra_script}
</body>
</html>
"""
    return html_text.encode("utf-8")


def slide_url_to_path(request_path: str) -> Path:
    path = urlparse(request_path).path
    if path == "/slide":
        return SLIDE_ROOT
    if not path.startswith("/slide/"):
        raise ValueError("Not a slide URL.")

    tail = path[len("/slide/"):]
    project_part, _, relative_part = tail.partition("/")
    project = validate_project_name(project_part)
    project_dir = require_slide_project(project)
    if not relative_part:
        return project_dir

    relative_text = unquote(relative_part)
    if "\x00" in relative_text:
        raise ValueError("Invalid slide asset path.")
    target = (project_dir / relative_text).resolve()
    try:
        target.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid slide asset path.") from exc
    return target



class WebHandler(SimpleHTTPRequestHandler):
    server_version = "VideoTemplateWeb/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def handle(self) -> None:
        try:
            super().handle()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return

    def translate_path(self, path: str) -> str:
        parsed_path = urlparse(path).path
        if parsed_path == "/slide" or parsed_path.startswith("/slide/"):
            try:
                return str(slide_url_to_path(path))
            except Exception:
                return str(REPO_ROOT / "__missing_slide_asset__")
        return super().translate_path(path)

    def log_message(self, format: str, *args: object) -> None:
        timestamp = time.strftime("%H:%M:%S")
        if format == '"%s" %s %s' and len(args) >= 3:
            request_line = str(args[0])
            parts = request_line.split()
            method = parts[0] if parts else self.command
            target = parts[1] if len(parts) > 1 else self.path
            status = str(args[1])
            size = str(args[2])
            try:
                status_code = int(status)
            except ValueError:
                status_code = 0
            if 200 <= status_code < 300:
                icon, status_style = "✅", "green"
            elif 300 <= status_code < 400:
                icon, status_style = "↪", "cyan"
            elif 400 <= status_code < 500:
                icon, status_style = "⚠️", "yellow"
            else:
                icon, status_style = "❌", "red"
            method_style = "blue" if method == "GET" else "magenta"
            size_text = "" if size == "-" else f" · {size}B"
            print(
                f"{icon} {color_text(timestamp, 'dim')}  "
                f"{color_text(method, 'bold', method_style)} {color_text(target, 'cyan')}  "
                f"{color_text(status, 'bold', status_style)}{color_text(size_text, 'dim')}",
                file=sys.stderr,
            )
            return

        print(f"ℹ️  {color_text(timestamp, 'dim')}  {format % args}", file=sys.stderr)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        parsed_path = urlparse(self.path).path
        if self.path.startswith("/web/") or (parsed_path.startswith("/slide/") and parsed_path.endswith((".js", ".css"))):
            self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def send_json(self, status: int, payload: object) -> None:
        data = json_dumps(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_html(self, status: int, data: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            raise ValueError("Missing request body.")
        if length > MAX_UPLOAD_BYTES * 4:
            raise ValueError("Request body is too large.")
        data = self.rfile.read(length)
        return json.loads(data.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            selected = (parse_qs(parsed.query).get("project") or [None])[0]
            self.send_html(200, render_home_html(selected))
            return

        if path in {"/create", "/create/"}:
            self.send_html(200, render_create_html(deck_allowed=is_loopback_client(self)))
            return

        if path == "/favicon.ico":
            self.send_redirect("/web/favicon.ico")
            return

        if path == "/web/brand-logo":
            logo_path = branding.branding_logo_path()
            if not logo_path:
                self.send_redirect("/web/logo-nicetechchannels.png")
                return
            data = logo_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(str(logo_path)))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path in {"/upload", "/upload/"}:
            selected = (parse_qs(parsed.query).get("project") or [None])[0]
            self.send_html(200, render_upload_html(selected))
            return

        if path in {"/upload-guide/youtube", "/upload-guide/youtube/"}:
            self.send_html(200, render_social_upload_guide_html("youtube"))
            return

        if path in {"/upload-guide/facebook", "/upload-guide/facebook/"}:
            self.send_html(200, render_social_upload_guide_html("facebook"))
            return

        if path in {"/elevenlabs-guide", "/elevenlabs-guide/"}:
            self.send_html(200, render_elevenlabs_guide_html())
            return

        if path == "/api/health":
            self.send_json(
                200,
                {
                    "ok": True,
                    "root": str(REPO_ROOT),
                    "source_root": str(SLIDE_ROOT),
                    "source_mode": source_root_mode(),
                    "projects": len(list_projects()),
                },
            )
            return

        if path == "/api/source-root":
            self.send_json(200, source_root_response())
            return

        if path == "/api/projects":
            self.send_json(200, {"projects": list_projects()})
            return

        if path == "/api/decks/status":
            payload = deck_status_payload()
            payload["client_allowed"] = is_loopback_client(self)
            self.send_json(200, payload)
            return

        if path == "/api/decks/drafts":
            slug = (parse_qs(parsed.query).get("slug") or [""])[0].strip().lower()
            if not slug or not DECK_SLUG_RE.match(slug):
                self.send_json(400, {"error": "Thiếu slug hợp lệ."})
                return
            drafts = read_deck_drafts(slug)
            if not drafts:
                self.send_json(404, {"error": f"Chưa có bản nháp script cho slide/{slug}/."})
                return
            self.send_json(200, {"slug": slug, "drafts": drafts})
            return

        if path == "/api/social/status":
            try:
                self.send_json(200, social_status())
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
            return

        if path == "/api/tts/elevenlabs/config":
            try:
                self.send_json(200, elevenlabs_public_config())
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
            return

        if path == "/api/social/upload-metadata":
            project = (parse_qs(parsed.query).get("project") or [""])[0]
            try:
                require_slide_project(project)
                self.send_json(200, build_upload_metadata(project))
            except FileNotFoundError as exc:
                self.send_json(404, {"error": str(exc)})
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
            return

        if path == "/api/social/youtube/connect":
            project = (parse_qs(parsed.query).get("project") or [""])[0]
            try:
                require_slide_project(project)
                self.send_redirect(start_youtube_oauth(project))
            except Exception as exc:
                self.send_html(400, social_callback_html("Không thể kết nối YouTube", str(exc), ok=False))
            return

        if path == "/api/social/youtube/callback":
            try:
                project = finish_youtube_oauth(parse_qs(parsed.query))
                message = f"YouTube đã kết nối cho project {project}." if project else "YouTube đã kết nối."
                self.send_html(200, social_callback_html("Đã kết nối YouTube", message))
            except Exception as exc:
                self.send_html(400, social_callback_html("Kết nối YouTube thất bại", str(exc), ok=False))
            return

        if path == "/api/preview-settings":
            project = (parse_qs(parsed.query).get("project") or [""])[0]
            try:
                settings = read_preview_settings(project)
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
                return
            self.send_json(200, {"project": project, "settings": settings})
            return

        if path == "/api/slide-script":
            project = (parse_qs(parsed.query).get("project") or [""])[0]
            try:
                result = read_slide_script(project)
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
                return
            self.send_json(200, result)
            return

        if path == "/api/costs":
            project = (parse_qs(parsed.query).get("project") or [""])[0]
            try:
                project_dir = require_slide_project(project)
            except FileNotFoundError as exc:
                self.send_json(404, {"error": str(exc)})
                return
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
                return
            try:
                report = cost_tracking.build_report(project_dir, cost_tracking.load_pricing())
            except Exception as exc:
                self.send_json(500, {"error": str(exc)})
                return
            self.send_json(200, report)
            return

        if path == "/render":
            self.send_redirect("/")
            return

        if path.startswith("/render/"):
            project = path.split("/render/", 1)[1].strip("/")
            self.send_redirect(f"/?project={quote(unquote(project))}")
            return

        if path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            job = get_job(job_id)
            if not job:
                self.send_json(404, {"error": "Job not found."})
                return
            self.send_json(200, job)
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/api/render":
            if parsed.path == "/api/preview-settings":
                try:
                    payload = self.read_json_body()
                    result = write_preview_settings(payload)
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/source-root":
                try:
                    if has_active_jobs():
                        raise RuntimeError("Đang có job render chạy, đợi xong rồi đổi source folder.")
                    payload = self.read_json_body()
                    source_root = str(payload.get("sourceRoot") or payload.get("source_root") or "").strip()
                    if not source_root:
                        raise ValueError("Missing source root.")
                    configure_source_root(source_root)
                    result = source_root_response()
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/source-root/select":
                try:
                    if has_active_jobs():
                        raise RuntimeError("Đang có job render chạy, đợi xong rồi đổi source folder.")
                    selected_root = choose_source_root_dialog()
                    configure_source_root(selected_root)
                    result = source_root_response()
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/preview-bgm":
                try:
                    payload = self.read_json_body()
                    result = upload_preview_bgm(payload)
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/tts/elevenlabs/config":
                try:
                    payload = self.read_json_body()
                    api_key = str(payload.get("api_key") or "").strip()
                    voice_id = str(payload.get("voice_id") or "").strip()
                    if api_key:
                        result = update_elevenlabs_api_key(api_key)
                    elif voice_id:
                        result = update_elevenlabs_voice_id(voice_id)
                    else:
                        raise ValueError("Missing ElevenLabs voice_id or api_key.")
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/slide-script":
                try:
                    payload = self.read_json_body()
                    result = write_slide_script(payload)
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path.startswith("/api/jobs/") and parsed.path.endswith("/cancel"):
                job_id = parsed.path.split("/api/jobs/", 1)[1].rsplit("/cancel", 1)[0].strip("/")
                try:
                    result = cancel_job(job_id)
                    if not result:
                        self.send_json(404, {"error": "Job not found."})
                        return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/decks":
                if not is_loopback_client(self):
                    self.send_json(403, {"error": "Chỉ cho phép tạo deck từ chính máy chạy server (localhost)."})
                    return
                available, reason, _mode = deck_feature_state()
                if not available:
                    self.send_json(503, {"error": deck_unavailable_message(reason), "reason": reason})
                    return
                try:
                    payload = self.read_json_body()
                    job = create_deck_job(payload)
                except ValueError as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(202, job)
                return

            if parsed.path == "/api/output/delete":
                try:
                    payload = self.read_json_body()
                    result = delete_project_output(payload)
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/output/reveal":
                try:
                    payload = self.read_json_body()
                    result = reveal_project_output(payload)
                except FileNotFoundError as exc:
                    self.send_json(404, {"error": str(exc)})
                    return
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/social/youtube/upload":
                try:
                    payload = self.read_json_body()
                    require_payload_project(payload)
                    result = youtube_upload_video(payload)
                except FileNotFoundError as exc:
                    self.send_json(404, {"error": str(exc)})
                    return
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/social/youtube/active-channel":
                try:
                    payload = self.read_json_body()
                    result = set_youtube_active_channel(str(payload.get("channelId") or payload.get("channel_id") or ""))
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/social/facebook/active-page":
                try:
                    payload = self.read_json_body()
                    result = set_facebook_active_page(str(payload.get("pageId") or payload.get("page_id") or ""))
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/social/facebook/config":
                try:
                    payload = self.read_json_body()
                    result = update_facebook_page_config(
                        str(payload.get("pageId") or payload.get("page_id") or ""),
                        str(payload.get("pageAccessToken") or payload.get("page_access_token") or ""),
                    )
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/social/facebook/upload":
                try:
                    payload = self.read_json_body()
                    require_payload_project(payload)
                    result = facebook_upload_video(payload)
                except FileNotFoundError as exc:
                    self.send_json(404, {"error": str(exc)})
                    return
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            if parsed.path == "/api/social/facebook/comment-source":
                try:
                    payload = self.read_json_body()
                    require_payload_project(payload)
                    result = facebook_comment_source(payload)
                except FileNotFoundError as exc:
                    self.send_json(404, {"error": str(exc)})
                    return
                except RuntimeError as exc:
                    self.send_json(409, {"error": str(exc)})
                    return
                except Exception as exc:
                    self.send_json(400, {"error": str(exc)})
                    return
                self.send_json(200, result)
                return

            self.send_json(404, {"error": "Unknown endpoint."})
            return

        try:
            payload = self.read_json_body()
            job = create_job(payload)
        except RuntimeError as exc:
            self.send_json(409, {"error": str(exc)})
            return
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})
            return

        self.send_json(202, job)


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the local slide render web UI.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--source-root",
        "--slide-root",
        default=None,
        help="Folder chứa các project slide, hoặc chính một project folder có index.html.",
    )
    args = parser.parse_args()
    try:
        source_root = (
            args.source_root
            or os.environ.get("NICETECHCHANNELS_SOURCE_ROOT")
            or os.environ.get("NICETECHCHANNELS_SLIDE_ROOT")
            # tên cũ trước khi đổi brand, giữ để máy đã set env không bị hỏng
            or os.environ.get("ESCBASE_SOURCE_ROOT")
            or os.environ.get("ESCBASE_SLIDE_ROOT")
        )
        configure_source_root(source_root or DEFAULT_SLIDE_ROOT)
    except Exception as exc:
        parser.error(str(exc))

    server = ThreadingHTTPServer((args.host, args.port), WebHandler)
    url = f"http://localhost:{args.port}"
    print()
    print(color_text("🚀  Bộ máy render slide local", "bold", "green"))
    print(f"   {color_text('🌐 Dashboard', 'cyan')}: {color_text(url, 'underline', 'bold')}")
    print(f"   {color_text('📂 Workspace', 'cyan')}: {REPO_ROOT}")
    print(f"   {color_text('🗂 Source root', 'cyan')}: {SLIDE_ROOT} ({source_root_mode()})")
    print(f"   {color_text('■ Dừng server', 'yellow')}: Ctrl+C")
    restart_cmd = r".\install.cmd" if sys.platform.startswith("win") else "python3 web_server.py"
    print(f"   {color_text('↻ Chạy lại server', 'yellow')}: {restart_cmd}")
    print()
    sys.stdout.flush()
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{color_text('👋 Đã dừng server.', 'yellow')}")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
