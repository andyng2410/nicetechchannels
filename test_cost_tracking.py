"""Unit tests cho cost_tracking.py — chạy: .venv/bin/python -m unittest test_cost_tracking -v (hoặc python3)."""

from __future__ import annotations

import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path

import cost_tracking as ct

TOKEN_LINE = "Token usage: total=3,501,933 input=3,473,366 (+ 3,327,232 cached) output=28,567 (reasoning 6,789)"
TOKEN_LINE_PLAIN = "Token usage: total=17723 input=17570 output=153"


class TokenUsageParserTest(unittest.TestCase):
    def test_full_line_with_commas(self):
        tokens = ct.parse_token_usage(f"blah\n{TOKEN_LINE}\n")
        self.assertEqual(tokens["total"], 3_501_933)
        self.assertEqual(tokens["input"], 3_473_366)
        self.assertEqual(tokens["cached_input"], 3_327_232)
        self.assertEqual(tokens["output"], 28_567)
        self.assertEqual(tokens["reasoning"], 6_789)

    def test_missing_cached_and_reasoning(self):
        tokens = ct.parse_token_usage(TOKEN_LINE_PLAIN)
        self.assertEqual(tokens["total"], 17_723)
        self.assertEqual(tokens["cached_input"], 0)
        self.assertEqual(tokens["reasoning"], 0)

    def test_last_match_wins(self):
        text = f"{TOKEN_LINE_PLAIN}\nnoise\n{TOKEN_LINE}\n"
        self.assertEqual(ct.parse_token_usage(text)["total"], 3_501_933)

    def test_no_match(self):
        self.assertIsNone(ct.parse_token_usage("no usage here"))
        self.assertIsNone(ct.parse_token_usage(None))

    def test_session_id(self):
        text = "banner\nsession id: 01A012E2-dd12-72e0-9371-54c9483bd7df\nmodel: gpt-5.6-sol\n"
        self.assertEqual(ct.parse_session_id(text), "01a012e2-dd12-72e0-9371-54c9483bd7df")
        self.assertEqual(ct.parse_model_line(text), "gpt-5.6-sol")


class RolloutParserTest(unittest.TestCase):
    def test_parse_rollout_fixture(self):
        lines = [
            {"type": "session_meta", "payload": {"cwd": "/repo", "originator": "codex_exec"}},
            {"type": "turn_context", "payload": {"model": "gpt-5.6-sol"}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 40,
                            "cache_write_input_tokens": 5,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 8,
                            "total_tokens": 120,
                        }
                    },
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 200,
                            "cached_input_tokens": 90,
                            "cache_write_input_tokens": 0,
                            "output_tokens": 50,
                            "reasoning_output_tokens": 10,
                            "total_tokens": 250,
                        }
                    },
                },
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            path.write_text(
                "hỏng-json\n" + "\n".join(json.dumps(line) for line in lines) + "\n",
                encoding="utf-8",
            )
            result = ct.parse_rollout(path)
        self.assertEqual(result["model"], "gpt-5.6-sol")
        self.assertEqual(result["cwd"], "/repo")
        self.assertEqual(result["originator"], "codex_exec")
        self.assertEqual(result["tokens"]["input"], 200)
        self.assertEqual(result["tokens"]["cached_input"], 90)
        self.assertEqual(result["tokens"]["total"], 250)


class SlideRefsTest(unittest.TestCase):
    def test_vietnamese_notes(self):
        self.assertEqual(ct.slide_refs_from_notes("Slide 3 chữ quá nhỏ; slide 5 đổi visual", 7), [3, 5])

    def test_range_dash(self):
        self.assertEqual(ct.slide_refs_from_notes("sửa slide 2-4 cho gọn", 7), [2, 3, 4])

    def test_range_den(self):
        self.assertEqual(ct.slide_refs_from_notes("slide 3 đến 5 đổi màu", 7), [3, 4, 5])

    def test_comma_list(self):
        self.assertEqual(ct.slide_refs_from_notes("slide 2, 4 cần chỉnh", 7), [2, 4])

    def test_clamp_and_empty(self):
        self.assertEqual(ct.slide_refs_from_notes("slide 9 lỗi", 7), [])
        self.assertEqual(ct.slide_refs_from_notes("đổi tông màu toàn deck", 7), [])
        self.assertEqual(ct.slide_refs_from_notes(None, 7), [])


class PricingTest(unittest.TestCase):
    def test_codex_usd(self):
        pricing = {"models": {"m": {"usd_per_1m_input": 1.0, "usd_per_1m_cached_input": 0.1, "usd_per_1m_output": 10.0}}}
        tokens = {"input": 1_000_000, "cached_input": 500_000, "output": 100_000}
        # 500k fresh * 1.0 + 500k cached * 0.1 + 100k out * 10.0 = 0.5 + 0.05 + 1.0
        self.assertAlmostEqual(ct.codex_usd(tokens, "m", pricing), 1.55)

    def test_codex_usd_cache_write(self):
        pricing = {"models": {"m": {"usd_per_1m_input": 5.0, "usd_per_1m_cached_input": 0.5,
                                    "usd_per_1m_cache_write_input": 6.25, "usd_per_1m_output": 30.0}}}
        tokens = {"input": 1_000_000, "cached_input": 600_000, "cache_write_input": 100_000, "output": 10_000}
        # 300k fresh * 5.0 + 600k cached * 0.5 + 100k write * 6.25 + 10k out * 30.0
        self.assertAlmostEqual(ct.codex_usd(tokens, "m", pricing), 1.5 + 0.3 + 0.625 + 0.3)
        # không có giá cache write riêng -> write tính như input thường
        del pricing["models"]["m"]["usd_per_1m_cache_write_input"]
        self.assertAlmostEqual(ct.codex_usd(tokens, "m", pricing), 1.5 + 0.3 + 0.5 + 0.3)

    def test_unknown_model(self):
        self.assertIsNone(ct.codex_usd({"input": 10}, "mystery", {"models": {}}))
        self.assertIsNone(ct.codex_usd(None, "m", {"models": {}}))

    def test_tts_usd(self):
        pricing = {"elevenlabs": {"usd_per_1k_chars": 0.10}, "edge": {"usd_per_1k_chars": 0.0}}
        self.assertAlmostEqual(ct.tts_usd(1834, "elevenlabs", pricing), 0.1834)
        self.assertEqual(ct.tts_usd(1834, "edge", pricing), 0.0)
        self.assertIsNone(ct.tts_usd(100, "unknown-engine", pricing))


class LedgerTest(unittest.TestCase):
    def test_append_and_load_skips_bad_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            ct.append_event(project, {"type": "render", "wall_s": 10})
            with ct.ledger_path(project).open("a", encoding="utf-8") as handle:
                handle.write("{dòng hỏng\n")
            ct.append_event(project, {"type": "tts", "chars": 5})
            events = ct.load_events(project)
        self.assertEqual([e["type"] for e in events], ["render", "tts"])
        self.assertTrue(all(e.get("id") and e.get("ts") for e in events))


def _append_worker(args):
    project, worker_idx, per_worker = args
    for i in range(per_worker):
        ct.append_event(project, {"type": "render", "wall_s": worker_idx * 1000 + i})


class ConcurrentAppendTest(unittest.TestCase):
    def test_multiprocess_append(self):
        workers, per_worker = 4, 25
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            with multiprocessing.Pool(workers) as pool:
                pool.map(_append_worker, [(project, w, per_worker) for w in range(workers)])
            events = ct.load_events(project)
        self.assertEqual(len(events), workers * per_worker)


class ReportTest(unittest.TestCase):
    def _project(self, tmp: str, lines: int = 3) -> Path:
        project = Path(tmp) / "proj"
        project.mkdir()
        (project / "script-90s.txt").write_text("\n".join(f"dòng {i}" for i in range(lines)), encoding="utf-8")
        return project

    def test_allocation_and_totals(self):
        pricing = json.loads(json.dumps(ct.DEFAULT_PRICING))
        pricing["models"]["m"] = {"usd_per_1m_input": 1.0, "usd_per_1m_cached_input": 0.1, "usd_per_1m_output": 10.0}
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, lines=3)
            ct.append_event(project, {
                "type": "codex_run", "stage": "build", "model": "m", "slide_count": 3,
                "tokens": {"input": 3_000_000, "cached_input": 0, "cache_write_input": 0,
                           "output": 300_000, "reasoning": 0, "total": 3_300_000},
                "duration_s": 60,
            })
            ct.append_event(project, {
                "type": "codex_run", "stage": "revise", "model": "m", "slide_count": 3,
                "notes": "slide 2 chữ nhỏ",
                "tokens": {"input": 1_000_000, "cached_input": 0, "cache_write_input": 0,
                           "output": 100_000, "reasoning": 0, "total": 1_100_000},
                "duration_s": 30,
            })
            ct.append_event(project, {
                "type": "tts", "engine": "elevenlabs", "mode": "full", "cached": False,
                "chars": 300, "per_line_chars": [100, 100, 100], "slide_count": 3,
            })
            ct.append_event(project, {"type": "render", "wall_s": 90, "per_slide_durations": [30, 30, 30], "slide_count": 3})
            report = ct.build_report(project, pricing)

        # build $6 chia đều 3 slide = 2; revise $2 dồn hết vào slide 2; tts $0.01/slide
        self.assertAlmostEqual(report["totals"]["usd_by_category"]["build"], 6.0)
        self.assertAlmostEqual(report["totals"]["usd_by_category"]["edit"], 2.0)
        self.assertAlmostEqual(report["totals"]["usd_by_category"]["tts"], 0.03)
        rows = report["per_slide"]
        self.assertAlmostEqual(rows[0]["usd_by_category"]["edit"], 0.0)
        self.assertAlmostEqual(rows[1]["usd_by_category"]["edit"], 2.0)
        self.assertAlmostEqual(rows[0]["usd"], 2.01, places=3)
        self.assertAlmostEqual(rows[1]["usd"], 4.01, places=3)
        self.assertEqual(rows[1]["tts_chars"], 100)
        self.assertAlmostEqual(rows[2]["render_s"], 30.0)
        self.assertEqual(report["lifecycle"]["edits"]["revise_count"], 1)
        self.assertEqual(report["lifecycle"]["rerenders"]["count"], 0)
        self.assertEqual(report["totals"]["tokens"]["total"], 4_400_000)
        self.assertTrue(report["pricing_known"])

    def test_slide_count_change_and_unknown_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, lines=2)  # hiện tại còn 2 slide
            ct.append_event(project, {
                "type": "codex_run", "stage": "build", "model": "mystery", "slide_count": 4,
                "tokens": {"input": 100, "cached_input": 0, "cache_write_input": 0,
                           "output": 10, "reasoning": 0, "total": 110},
            })
            ct.append_event(project, {"type": "codex_run", "stage": "build", "model": "mystery",
                                      "tokens": None, "usage_missing": True})
            report = ct.build_report(project, ct.load_pricing(path=Path(tmp) / "khong-ton-tai.json"))

        self.assertEqual(len(report["per_slide"]), 4)
        self.assertTrue(report["per_slide"][3]["removed"])
        self.assertFalse(report["per_slide"][1]["removed"])
        self.assertFalse(report["pricing_known"])
        self.assertTrue(any("mystery" in w for w in report["warnings"]))
        self.assertTrue(any("token usage" in w for w in report["warnings"]))

    def test_cached_tts_and_rerenders(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, lines=2)
            ct.append_event(project, {"type": "tts", "engine": "elevenlabs", "cached": False,
                                      "chars": 200, "per_line_chars": [100, 100], "slide_count": 2})
            ct.append_event(project, {"type": "render", "wall_s": 60, "per_slide_durations": [30, 30], "slide_count": 2})
            ct.append_event(project, {"type": "tts", "engine": "elevenlabs", "cached": True,
                                      "chars": 0, "per_line_chars": [100, 100], "slide_count": 2})
            ct.append_event(project, {"type": "render", "wall_s": 60, "per_slide_durations": [30, 30], "slide_count": 2})
            ct.append_event(project, {"type": "output_delete", "had_paid_voiceover": True})
            report = ct.build_report(project, ct.load_pricing(path=Path(tmp) / "khong-ton-tai.json"))

        self.assertEqual(report["totals"]["tts_calls"], 1)
        self.assertEqual(report["totals"]["tts_calls_cached"], 1)
        self.assertEqual(report["lifecycle"]["rerenders"]["count"], 1)
        self.assertAlmostEqual(report["lifecycle"]["rerenders"]["tts_usd_extra"], 0.0)
        self.assertTrue(any("mua lại" in w for w in report["warnings"]))
        # tts_chars chỉ đếm lần bill thật, không đếm cache hit
        self.assertEqual(report["per_slide"][0]["tts_chars"], 100)


if __name__ == "__main__":
    unittest.main()
