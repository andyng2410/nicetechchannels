#!/usr/bin/env python3
"""Chụp QA toàn bộ slide ở 390x693 với mọi reveal đã hiện.

Dùng sau khi validate_slide.py PASS:

    .venv/bin/python capture_slides.py slide/<project>

Ảnh lưu vào /tmp/nicetechchannels-qa/<project>/slideN.png (side panels/preview UI đã ẩn).
"""

import argparse
import asyncio
import sys
from pathlib import Path


async def capture(slide_dir: Path, out_dir: Path, settle_ms: int) -> int:
    from playwright.async_api import async_playwright

    uri = (slide_dir / "index.html").resolve().as_uri()
    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 693}, device_scale_factor=2)
        await page.goto(uri, wait_until="networkidle")
        await page.add_style_tag(
            content=".side-controls, .script-panel, .audio-panel { display: none !important; }"
        )
        total = await page.evaluate("document.querySelectorAll('.slide').length")
        for i in range(total):
            await page.evaluate(
                """(i) => {
                  document.querySelectorAll('.slide').forEach((s, idx) => {
                    s.classList.toggle('active', idx === i);
                    s.style.opacity = idx === i ? '1' : '0';
                  });
                  const slide = document.querySelectorAll('.slide')[i];
                  slide.querySelectorAll('.slide-element').forEach(el => el.classList.add('visible'));
                  slide.querySelectorAll('.highlightable').forEach(el => el.classList.add('highlighted'));
                  slide.querySelectorAll('.lightable').forEach(el => {
                    el.classList.add('lit-red', 'lit-yellow', 'lit-green');
                  });
                }""",
                i,
            )
            await page.wait_for_timeout(settle_ms)
            await page.screenshot(path=str(out_dir / f"slide{i + 1}.png"))
        await browser.close()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slide_dir", help="slide/<project>")
    parser.add_argument("--out", default=None, help="Thư mục output (default /tmp/nicetechchannels-qa/<project>)")
    parser.add_argument("--settle-ms", type=int, default=1500, help="Chờ animation ổn định trước khi chụp")
    args = parser.parse_args()

    slide_dir = Path(args.slide_dir)
    if not (slide_dir / "index.html").exists():
        sys.exit(f"Không thấy index.html trong {slide_dir}")

    out_dir = Path(args.out) if args.out else Path("/tmp/nicetechchannels-qa") / slide_dir.name
    total = asyncio.run(capture(slide_dir, out_dir, args.settle_ms))
    print(f"Đã chụp {total} slide -> {out_dir}")


if __name__ == "__main__":
    main()
