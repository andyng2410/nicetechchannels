"""Single source of truth cho brand kênh: tên, handle, tagline, logo, câu outro.

Đọc config/branding.json (gitignore) đè lên defaults; thiếu file = NiceTechChannels.
Mọi module (web_server, social_upload.metadata, auto_render...) import từ đây,
không hardcode tên kênh ở chỗ khác. Config đọc một lần lúc import — đổi config
phải restart process (web_server, deck_host_runner).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

BRANDING_DEFAULTS = {
    "name": "NiceTechChannels",
    "handle": "@nicetechchannels",
    "tagline": "Tin công nghệ và AI mỗi tuần",
    "outro_line": "",
    "logo": "",
}


def load_branding() -> dict:
    merged = dict(BRANDING_DEFAULTS)
    try:
        raw = json.loads((REPO_ROOT / "config" / "branding.json").read_text(encoding="utf-8"))
    except Exception:
        raw = None
    if isinstance(raw, dict):
        for key in BRANDING_DEFAULTS:
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                merged[key] = value.strip()
    return merged


BRANDING = load_branding()

OUTRO_SCRIPT_LINE = BRANDING["outro_line"] or (
    f"Hãy theo dõi ngay {BRANDING['name']}. Đăng ký kênh để không bỏ lỡ những tin tức mới nhất về công nghệ và AI."
)


def branding_logo_path() -> Path | None:
    logo = BRANDING.get("logo") or ""
    if not logo:
        return None
    path = Path(logo).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path if path.is_file() else None


def brand_hashtag() -> str:
    return re.sub(r"[^0-9A-Za-z_]", "", BRANDING["name"]) or "NiceTechChannels"
