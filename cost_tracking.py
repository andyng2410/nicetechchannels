"""Cost ledger cho pipeline slide: ghi token/chars/giây per event, tính $ lúc đọc.

Ledger là file JSONL append-only tại slide/<project>/cost-ledger.jsonl — nằm ở
project root (sống sót qua /api/output/delete, share qua bind mount ./slide nên
cả host runner lẫn container đều ghi được). Mỗi event 1 dòng, 1 lần write ở chế
độ append; reader bỏ qua dòng hỏng nên 2 writer đồng thời tối đa làm hỏng 1 dòng.

Nguyên tắc: event lưu SỐ LƯỢNG THÔ (tokens, chars, giây) làm source of truth;
USD chỉ là snapshot nullable — report luôn tính lại từ bảng giá của bên đọc,
vì config/pricing.json không share giữa host và container (config/ là volume).
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path

LEDGER_NAME = "cost-ledger.jsonl"
SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_PRICING_PATH = REPO_ROOT / "config" / "pricing.json"

# Giá model là API-equivalent (user chạy Codex qua subscription): chỉnh trong
# config/pricing.json (copy từ pricing.example.json), defaults này để container
# không có pricing.json vẫn ra số. Giá Sol theo bảng giá OpenAI 08/2026:
# $5 input / $0.50 cached (10%) / $30 output per 1M; cache write 1.25x input.
DEFAULT_PRICING = {
    "models": {
        "gpt-5.6-sol": {
            "usd_per_1m_input": 5.0,
            "usd_per_1m_cached_input": 0.5,
            "usd_per_1m_cache_write_input": 6.25,
            "usd_per_1m_output": 30.0,
        },
    },
    "elevenlabs": {"usd_per_1k_chars": 0.10},
    "edge": {"usd_per_1k_chars": 0.0},
    "machine": {"usd_per_hour": 0.0},
}

# Stage codex -> nhóm chi phí trong report.
STAGE_CATEGORY = {"drafts": "build", "build": "build", "auto": "build", "revise": "edit"}


# --- Ledger ---------------------------------------------------------------


def ledger_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / LEDGER_NAME


def append_event(project_dir: Path | str, event: dict) -> dict:
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload.setdefault("schema", SCHEMA_VERSION)
    payload.setdefault("id", uuid.uuid4().hex[:12])
    payload["ts"] = float(payload.get("ts") or time.time())
    payload.setdefault("ts_iso", time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(payload["ts"])))
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    with ledger_path(project_dir).open("a", encoding="utf-8") as handle:
        handle.write(line)
    return payload


def safe_append_event(project_dir: Path | str, event: dict) -> dict | None:
    """append_event nhưng nuốt lỗi: cost tracking không bao giờ được làm fail job."""
    try:
        return append_event(project_dir, event)
    except Exception as exc:  # noqa: BLE001
        print(f"[cost] Không ghi được cost-ledger cho {project_dir}: {exc}")
        return None


def load_events(project_dir: Path | str) -> list[dict]:
    path = ledger_path(project_dir)
    if not path.is_file():
        return []
    events: list[dict] = []
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("type"):
            events.append(data)
    events.sort(key=lambda item: float(item.get("ts") or 0))
    return events


# --- Parsers (stdout codex exec + rollout JSONL) --------------------------

TOKEN_USAGE_RE = re.compile(
    r"Token usage:\s*total=([\d,]+)\s+input=([\d,]+)"
    r"(?:\s*\(\+\s*([\d,]+)\s+cached\))?"
    r"\s+output=([\d,]+)"
    r"(?:\s*\(reasoning\s+([\d,]+)\))?",
    re.IGNORECASE,
)
SESSION_ID_RE = re.compile(
    r"session id:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)
MODEL_LINE_RE = re.compile(r"^\s*model:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def _to_int(raw: str | None) -> int:
    if not raw:
        return 0
    return int(str(raw).replace(",", ""))


def parse_token_usage(text: str | None) -> dict | None:
    matches = TOKEN_USAGE_RE.findall(text or "")
    if not matches:
        return None
    total, input_tokens, cached, output, reasoning = matches[-1]
    return {
        "input": _to_int(input_tokens),
        "cached_input": _to_int(cached),
        "cache_write_input": 0,
        "output": _to_int(output),
        "reasoning": _to_int(reasoning),
        "total": _to_int(total),
    }


def parse_session_id(text: str | None) -> str | None:
    match = SESSION_ID_RE.search(text or "")
    return match.group(1).lower() if match else None


def parse_model_line(text: str | None) -> str | None:
    match = MODEL_LINE_RE.search(text or "")
    return match.group(1) if match else None


def find_rollout_file(session_id: str | None, sessions_root: Path | str | None = None) -> Path | None:
    if not session_id:
        return None
    root = Path(sessions_root) if sessions_root else Path.home() / ".codex" / "sessions"
    if not root.is_dir():
        return None
    matches = sorted(root.glob(f"*/*/*/rollout-*-{session_id}.jsonl"))
    return matches[-1] if matches else None


def parse_rollout(path: Path | str) -> dict | None:
    """Đọc rollout JSONL của codex: lấy token_count cuối, model, cwd, originator."""
    tokens = None
    model = None
    cwd = None
    originator = None
    try:
        with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(data, dict):
                    continue
                payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
                dtype = data.get("type")
                if dtype == "session_meta":
                    cwd = payload.get("cwd") or cwd
                    originator = payload.get("originator") or originator
                elif dtype == "turn_context":
                    model = payload.get("model") or model
                elif dtype == "event_msg" and payload.get("type") == "token_count":
                    info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
                    usage = info.get("total_token_usage") if isinstance(info.get("total_token_usage"), dict) else None
                    if usage:
                        tokens = {
                            "input": int(usage.get("input_tokens") or 0),
                            "cached_input": int(usage.get("cached_input_tokens") or 0),
                            "cache_write_input": int(usage.get("cache_write_input_tokens") or 0),
                            "output": int(usage.get("output_tokens") or 0),
                            "reasoning": int(usage.get("reasoning_output_tokens") or 0),
                            "total": int(usage.get("total_tokens") or 0),
                        }
    except OSError:
        return None
    if tokens is None and model is None:
        return None
    return {"tokens": tokens, "model": model, "cwd": cwd, "originator": originator}


SLIDE_REF_RE = re.compile(
    r"slide\s*#?\s*(\d+)(?:\s*(?:-|–|—|đến|to)\s*(\d+))?((?:\s*,\s*\d+)+)?",
    re.IGNORECASE,
)


def slide_refs_from_notes(notes: str | None, slide_count: int | None) -> list[int]:
    """Rút số slide (1-based) từ notes revise: "slide 3", "slide 2-4", "slide 3 đến 5", "slide 2, 4"."""
    if not notes:
        return []
    refs: set[int] = set()
    for match in SLIDE_REF_RE.finditer(notes):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if end < start:
            start, end = end, start
        refs.update(range(start, end + 1))
        if match.group(3):
            refs.update(int(extra) for extra in re.findall(r"\d+", match.group(3)))
    if slide_count:
        refs = {n for n in refs if 1 <= n <= slide_count}
    else:
        refs = {n for n in refs if n >= 1}
    return sorted(refs)


# --- Pricing --------------------------------------------------------------


def load_pricing(path: Path | str | None = None) -> dict:
    pricing = json.loads(json.dumps(DEFAULT_PRICING))
    pricing["_source"] = "builtin-defaults"
    candidate = Path(path) if path else DEFAULT_PRICING_PATH
    if candidate.is_file():
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return pricing
        if isinstance(data, dict):
            for key in ("elevenlabs", "edge", "machine"):
                if isinstance(data.get(key), dict):
                    pricing[key].update(data[key])
            if isinstance(data.get("models"), dict):
                for name, rates in data["models"].items():
                    if isinstance(rates, dict):
                        pricing["models"][name] = rates
            pricing["_source"] = str(candidate)
    return pricing


def codex_usd(tokens: dict | None, model: str | None, pricing: dict) -> float | None:
    if not tokens:
        return None
    rates = (pricing.get("models") or {}).get(str(model or ""))
    if not isinstance(rates, dict):
        return None
    try:
        input_rate = float(rates["usd_per_1m_input"])
        cached_rate = float(rates["usd_per_1m_cached_input"])
        output_rate = float(rates["usd_per_1m_output"])
    except (KeyError, TypeError, ValueError):
        return None
    try:
        cache_write_rate = float(rates["usd_per_1m_cache_write_input"])
    except (KeyError, TypeError, ValueError):
        cache_write_rate = input_rate  # không có giá riêng thì cache write tính như input thường
    cached_input = int(tokens.get("cached_input") or 0)
    cache_write = int(tokens.get("cache_write_input") or 0)
    output = int(tokens.get("output") or 0)
    # input_tokens của codex là tổng input, gồm cả cached read và cache write
    fresh_input = max(0, int(tokens.get("input") or 0) - cached_input - cache_write)
    return (
        fresh_input * input_rate
        + cached_input * cached_rate
        + cache_write * cache_write_rate
        + output * output_rate
    ) / 1_000_000


def tts_usd(chars: int | None, engine: str, pricing: dict) -> float | None:
    rates = pricing.get(engine)
    if not isinstance(rates, dict):
        return None
    try:
        per_1k = float(rates["usd_per_1k_chars"])
    except (KeyError, TypeError, ValueError):
        return None
    return max(0, int(chars or 0)) * per_1k / 1000.0


def render_usd(wall_s: float | None, pricing: dict) -> float:
    try:
        per_hour = float((pricing.get("machine") or {}).get("usd_per_hour") or 0.0)
    except (TypeError, ValueError):
        per_hour = 0.0
    return max(0.0, float(wall_s or 0.0)) * per_hour / 3600.0


# --- Report ---------------------------------------------------------------


def project_cost_totals(project_dir: Path | str, pricing: dict | None = None) -> dict | None:
    """Tổng gọn cho danh sách project: {usd, tokens, pricing_known}. None nếu chưa có ledger."""
    events = load_events(project_dir)
    if not events:
        return None
    pricing = pricing or load_pricing()
    usd = 0.0
    tokens = 0
    known = True
    for event in events:
        etype = event.get("type")
        if etype == "codex_run":
            event_tokens = event.get("tokens") if isinstance(event.get("tokens"), dict) else None
            tokens += int((event_tokens or {}).get("total") or 0)
            event_usd = codex_usd(event_tokens, str(event.get("model") or ""), pricing)
            if event_tokens and event_usd is None:
                known = False
            usd += event_usd or 0.0
        elif etype == "tts":
            event_usd = tts_usd(event.get("chars"), str(event.get("engine") or ""), pricing)
            if event_usd is None:
                known = False
            usd += event_usd or 0.0
        elif etype == "render":
            usd += render_usd(event.get("wall_s"), pricing)
    return {"usd": round(usd, 2), "tokens": tokens, "pricing_known": known}


def count_script_lines(project_dir: Path | str) -> int | None:
    script = Path(project_dir) / "script-90s.txt"
    if not script.is_file():
        return None
    try:
        lines = [line.strip() for line in script.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return None
    return len(lines) or None


def _timing_durations(project_dir: Path) -> list[float] | None:
    timing = project_dir / "output" / "timing.json"
    if not timing.is_file():
        return None
    try:
        data = json.loads(timing.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, list) or not data:
        return None
    try:
        return [max(0.0, float(item.get("duration") or 0)) for item in data]
    except (TypeError, AttributeError):
        return None


def _even_weights(count: int) -> list[float]:
    if count <= 0:
        return []
    return [1.0 / count] * count


def _normalized(values: list[float] | None) -> list[float] | None:
    if not values:
        return None
    total = sum(max(0.0, float(v)) for v in values)
    if total <= 0:
        return None
    return [max(0.0, float(v)) / total for v in values]


def _event_weights(event: dict, current_count: int | None, timing_durations: list[float] | None) -> list[float]:
    """Trọng số phân bổ per-slide (index 0 = slide 1) cho một event. Rỗng = không phân bổ được."""
    etype = event.get("type")
    slide_count = event.get("slide_count") or current_count or 0
    if etype == "tts":
        weights = _normalized(event.get("per_line_chars"))
        if weights:
            return weights
        return _even_weights(int(slide_count))
    if etype == "render":
        weights = _normalized(event.get("per_slide_durations")) or _normalized(timing_durations)
        if weights:
            return weights
        return _even_weights(int(slide_count))
    if etype == "codex_run":
        count = int(slide_count)
        if event.get("stage") == "revise":
            refs = slide_refs_from_notes(event.get("notes"), count or None)
            if refs:
                size = max(count, max(refs))
                weights = [0.0] * size
                for ref in refs:
                    weights[ref - 1] = 1.0 / len(refs)
                return weights
        return _even_weights(count)
    return []


def build_report(project_dir: Path | str, pricing: dict | None = None) -> dict:
    project_dir = Path(project_dir)
    pricing = pricing or load_pricing()
    events = load_events(project_dir)
    current_count = count_script_lines(project_dir)
    timing_durations = _timing_durations(project_dir)
    warnings: list[str] = []
    if pricing.get("_source") == "builtin-defaults":
        warnings.append("Đang dùng bảng giá mặc định built-in; copy config/pricing.example.json thành config/pricing.json để chỉnh giá.")

    table_size = max(
        [int(e.get("slide_count") or 0) for e in events] + [current_count or 0] + [0]
    )
    categories = ("build", "edit", "tts", "render")
    per_slide = [
        {
            "slide": i + 1,
            "tokens_total": 0.0,
            "usd": 0.0,
            "usd_by_category": {cat: 0.0 for cat in categories},
            "tts_chars": 0,
            "render_s": 0.0,
            "removed": bool(current_count and i + 1 > current_count),
        }
        for i in range(table_size)
    ]

    totals_tokens = {"input": 0, "cached_input": 0, "cache_write_input": 0, "output": 0, "reasoning": 0, "total": 0}
    totals_usd_by_category = {cat: 0.0 for cat in categories}
    usd_incomplete = False
    unknown_models: set[str] = set()
    usage_missing_count = 0
    codex_runs = tts_calls = tts_calls_cached = renders = 0
    codex_s = render_s_total = 0.0

    codex_build_usd = codex_build_tokens = 0.0
    codex_build_events = 0
    codex_edit_usd = codex_edit_tokens = 0.0
    revise_count = 0
    tts_billed_events = 0
    first_tts_usd = extra_tts_usd = 0.0
    first_render_usd = 0.0
    output_delete_count = 0

    for event in events:
        etype = event.get("type")
        usd = None
        category = None

        if etype == "codex_run":
            codex_runs += 1
            codex_s += float(event.get("duration_s") or 0)
            tokens = event.get("tokens") if isinstance(event.get("tokens"), dict) else None
            if tokens:
                for key in totals_tokens:
                    totals_tokens[key] += int(tokens.get(key) or 0)
            else:
                usage_missing_count += 1
            model = str(event.get("model") or "")
            usd = codex_usd(tokens, model, pricing)
            if tokens and usd is None:
                unknown_models.add(model or "(không rõ model)")
                usd_incomplete = True
            category = STAGE_CATEGORY.get(str(event.get("stage") or ""), "build")
            if category == "edit":
                revise_count += 1
                codex_edit_usd += usd or 0.0
                codex_edit_tokens += (tokens or {}).get("total") or 0
            else:
                codex_build_events += 1
                codex_build_usd += usd or 0.0
                codex_build_tokens += (tokens or {}).get("total") or 0
        elif etype == "tts":
            engine = str(event.get("engine") or "edge")
            chars = int(event.get("chars") or 0)
            usd = tts_usd(chars, engine, pricing)
            if usd is None:
                usd_incomplete = True
            category = "tts"
            if event.get("cached") or chars <= 0:
                tts_calls_cached += 1
            else:
                tts_calls += 1
                tts_billed_events += 1
                if tts_billed_events == 1:
                    first_tts_usd = usd or 0.0
                else:
                    extra_tts_usd += usd or 0.0
        elif etype == "render":
            renders += 1
            wall_s = float(event.get("wall_s") or 0)
            render_s_total += wall_s
            usd = render_usd(wall_s, pricing)
            category = "render"
            if renders == 1:
                first_render_usd = usd
        elif etype == "output_delete":
            output_delete_count += 1
            continue
        else:
            continue

        if usd is not None and category:
            totals_usd_by_category[category] += usd

        weights = _event_weights(event, current_count, timing_durations)
        if not weights:
            continue
        tokens_total = float(((event.get("tokens") or {}).get("total") or 0)) if etype == "codex_run" else 0.0
        for idx, weight in enumerate(weights):
            if idx >= len(per_slide) or weight <= 0:
                continue
            row = per_slide[idx]
            if usd is not None:
                row["usd"] += usd * weight
                if category:
                    row["usd_by_category"][category] += usd * weight
            row["tokens_total"] += tokens_total * weight
            if etype == "tts":
                per_line = event.get("per_line_chars") or []
                if idx < len(per_line) and not event.get("cached"):
                    row["tts_chars"] += int(per_line[idx] or 0)
            if etype == "render":
                row["render_s"] += float(event.get("wall_s") or 0) * weight

    if usage_missing_count:
        warnings.append(f"{usage_missing_count} lần chạy Codex không lấy được token usage (đã đếm hoạt động, thiếu số token).")
    if unknown_models:
        warnings.append("Model chưa có trong bảng giá (usd bỏ trống): " + ", ".join(sorted(unknown_models)))
    if output_delete_count:
        warnings.append(f"output/ đã bị xoá {output_delete_count} lần — audio ElevenLabs trả phí phải mua lại nếu render tiếp.")
    if not table_size and events:
        warnings.append("Không xác định được số slide để phân bổ per-slide.")

    for row in per_slide:
        row["tokens_total"] = int(round(row["tokens_total"]))
        row["usd"] = round(row["usd"], 4)
        row["usd_by_category"] = {cat: round(val, 4) for cat, val in row["usd_by_category"].items()}
        row["render_s"] = round(row["render_s"], 1)

    totals_usd = round(sum(totals_usd_by_category.values()), 4)
    return {
        "project": project_dir.name,
        "slide_count": current_count,
        "pricing_source": pricing.get("_source"),
        "pricing_known": not usd_incomplete,
        "warnings": warnings,
        "totals": {
            "tokens": totals_tokens,
            "usd": totals_usd,
            "usd_by_category": {cat: round(val, 4) for cat, val in totals_usd_by_category.items()},
            "codex_runs": codex_runs,
            "tts_calls": tts_calls,
            "tts_calls_cached": tts_calls_cached,
            "renders": renders,
            "codex_s": round(codex_s, 1),
            "render_s": round(render_s_total, 1),
        },
        "per_slide": per_slide,
        "lifecycle": {
            "first_build": {
                "usd": round(codex_build_usd + first_tts_usd + first_render_usd, 4),
                "tokens": int(codex_build_tokens),
                "events": codex_build_events,
            },
            "edits": {
                "usd": round(codex_edit_usd, 4),
                "tokens": int(codex_edit_tokens),
                "revise_count": revise_count,
            },
            "rerenders": {
                "count": max(0, renders - 1),
                "tts_usd_extra": round(extra_tts_usd, 4),
                "render_s": round(render_s_total, 1),
            },
        },
        "events_count": len(events),
    }
