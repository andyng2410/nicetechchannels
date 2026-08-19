#!/usr/bin/env python3
"""In báo cáo chi phí per-slide từ cost-ledger.jsonl của một project.

Usage:
    python3 cost_report.py slide/<project> [--json] [--pricing config/pricing.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cost_tracking


def fmt_usd(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:,.4f}" if value < 1 else f"${value:,.2f}"


def fmt_tokens(value: int | float | None) -> str:
    value = int(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def print_table(rows: list[list[str]], headers: list[str]) -> None:
    widths = [max(len(str(cell)) for cell in [header] + [row[i] for row in rows]) for i, header in enumerate(headers)]
    line = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    print(line)
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Báo cáo chi phí per-slide (token + USD) từ cost-ledger.jsonl.")
    parser.add_argument("project_dir", help="Đường dẫn project, vd slide/<tên>")
    parser.add_argument("--json", action="store_true", help="In report JSON thay vì bảng")
    parser.add_argument("--pricing", help="Đường dẫn pricing.json (mặc định config/pricing.json rồi defaults built-in)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"Không thấy thư mục project: {project_dir}", file=sys.stderr)
        return 1
    if not cost_tracking.ledger_path(project_dir).is_file():
        print(f"Chưa có {cost_tracking.LEDGER_NAME} trong {project_dir} — chưa có hoạt động nào được ghi.", file=sys.stderr)
        return 1

    pricing = cost_tracking.load_pricing(args.pricing)
    report = cost_tracking.build_report(project_dir, pricing)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    totals = report["totals"]
    lifecycle = report["lifecycle"]
    print(f"=== Chi phí project: {report['project']} ===")
    print(f"Bảng giá: {report['pricing_source']}")
    print(
        f"Tổng: {fmt_usd(totals['usd'])}"
        + (" (thiếu giá một phần)" if not report["pricing_known"] else "")
        + f" | tokens {fmt_tokens(totals['tokens']['total'])}"
        f" (input {fmt_tokens(totals['tokens']['input'])}, cached {fmt_tokens(totals['tokens']['cached_input'])},"
        f" output {fmt_tokens(totals['tokens']['output'])})"
    )
    by_cat = totals["usd_by_category"]
    print(
        f"Theo nhóm: build {fmt_usd(by_cat['build'])} · sửa {fmt_usd(by_cat['edit'])}"
        f" · TTS {fmt_usd(by_cat['tts'])} · render {fmt_usd(by_cat['render'])}"
    )
    print(
        f"Hoạt động: {totals['codex_runs']} lần Codex ({totals['codex_s']:.0f}s)"
        f" · {totals['tts_calls']} lần TTS bill + {totals['tts_calls_cached']} cache hit"
        f" · {totals['renders']} lần render ({totals['render_s']:.0f}s)"
    )
    print()

    if report["per_slide"]:
        rows = []
        for row in report["per_slide"]:
            cats = row["usd_by_category"]
            rows.append([
                f"{row['slide']}" + (" (đã xoá)" if row["removed"] else ""),
                fmt_tokens(row["tokens_total"]),
                fmt_usd(cats["build"]),
                fmt_usd(cats["edit"]),
                fmt_usd(cats["tts"]),
                f"{row['render_s']:.0f}s",
                fmt_usd(row["usd"]),
            ])
        print_table(rows, ["Slide", "Tokens", "$ build", "$ sửa", "$ TTS", "Render", "$ tổng"])
        print()

    print("=== Vòng đời ===")
    fb = lifecycle["first_build"]
    ed = lifecycle["edits"]
    rr = lifecycle["rerenders"]
    print(f"Build lần đầu: {fmt_usd(fb['usd'])} ({fb['events']} lần Codex, {fmt_tokens(fb['tokens'])} tokens)")
    print(f"Chỉnh sửa:     {fmt_usd(ed['usd'])} ({ed['revise_count']} lần revise, {fmt_tokens(ed['tokens'])} tokens)")
    print(f"Re-render:     {rr['count']} lần, TTS bill thêm {fmt_usd(rr['tts_usd_extra'])}, tổng {rr['render_s']:.0f}s render")

    if report["warnings"]:
        print("\n=== Cảnh báo ===")
        for warning in report["warnings"]:
            print(f"⚠ {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
