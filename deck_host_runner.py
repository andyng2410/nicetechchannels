#!/usr/bin/env python3
"""Host runner cho deck builder: chạy trên máy host (nơi có Codex CLI + đăng nhập subscription).

Web UI trong container ghi yêu cầu vào slide/.deck-runner/jobs/<id>.request.json;
runner này nhặt yêu cầu, spawn `codex exec` trên host, stream log ra file cho
web_server tail về UI, và tôn trọng file <id>.cancel để dừng job.

Chạy: python3 deck_host_runner.py   (trong thư mục repo, để chạy nền: thêm & hoặc dùng tmux)
Dừng: Ctrl+C — job codex đang chạy (nếu có) sẽ bị dừng theo.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RUNNER_ROOT = REPO_ROOT / "slide" / ".deck-runner"
JOBS_ROOT = RUNNER_ROOT / "jobs"
HEARTBEAT_PATH = RUNNER_ROOT / "heartbeat.json"
HEARTBEAT_INTERVAL = 3.0
POLL_INTERVAL = 1.0

sys.path.insert(0, str(REPO_ROOT))
import cost_tracking  # noqa: E402
from web_server import build_deck_command, codex_binary_path, load_agent_config  # noqa: E402


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def write_heartbeat() -> None:
    RUNNER_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {"pid": os.getpid(), "codex_path": codex_binary_path(), "updated_at": time.time()}
    tmp = HEARTBEAT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.rename(HEARTBEAT_PATH)


def write_status(job_id: str, payload: dict) -> None:
    path = JOBS_ROOT / f"{job_id}.status.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.rename(path)


def terminate_group(proc: subprocess.Popen) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, sig)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def run_deck_job(request_path: Path) -> None:
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"Bỏ qua request hỏng {request_path.name}: {exc}")
        request_path.unlink(missing_ok=True)
        return

    job_id = str(request.get("job_id") or request_path.name.split(".", 1)[0])
    slug = str(request.get("slug") or "?")
    prompt = str(request.get("prompt") or "")
    try:
        timeout_minutes = max(5, int(request.get("timeout_minutes")))
    except (TypeError, ValueError):
        timeout_minutes = 90

    log_path = JOBS_ROOT / f"{job_id}.log"
    cancel_path = JOBS_ROOT / f"{job_id}.cancel"

    if not prompt:
        log_path.write_text("Request thiếu prompt.\n", encoding="utf-8")
        write_status(job_id, {"status": "exited", "returncode": -1, "finished_at": time.time()})
        request_path.unlink(missing_ok=True)
        return

    config = load_agent_config()
    try:
        cmd = build_deck_command(config)
    except Exception as exc:
        log_path.write_text(f"Không dựng được lệnh codex: {exc}\n", encoding="utf-8")
        write_status(job_id, {"status": "exited", "returncode": -1, "finished_at": time.time()})
        request_path.unlink(missing_ok=True)
        return

    log(f"Bắt đầu deck job {job_id} (slug {slug}, timeout {timeout_minutes} phút)")
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(cmd)}\n(host runner pid {os.getpid()})\n\n")
        log_file.flush()
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                start_new_session=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
        except Exception as exc:
            log_file.write(f"Không spawn được codex: {exc}\n")
            write_status(job_id, {"status": "exited", "returncode": -1, "finished_at": time.time()})
            request_path.unlink(missing_ok=True)
            return

        write_status(job_id, {"status": "running", "pid": proc.pid, "started_at": time.time()})
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except Exception as exc:
            log_file.write(f"Không gửi được prompt qua stdin: {exc}\n")
            log_file.flush()

        def stream_stdout() -> None:
            try:
                for line in proc.stdout:
                    log_file.write(line)
                    log_file.flush()
            except Exception:
                pass

        reader = threading.Thread(target=stream_stdout, daemon=True)
        reader.start()

        deadline = time.time() + timeout_minutes * 60
        cancelled = False
        while proc.poll() is None:
            if cancel_path.exists():
                log_file.write("\nNhận tín hiệu dừng từ web UI, đang kill codex...\n")
                log_file.flush()
                terminate_group(proc)
                cancelled = True
                break
            if time.time() > deadline:
                log_file.write(f"\nQuá {timeout_minutes} phút, runner tự dừng codex.\n")
                log_file.flush()
                terminate_group(proc)
                break
            write_heartbeat()
            time.sleep(POLL_INTERVAL)

        reader.join(timeout=10)
        returncode = proc.wait()

    # Đọc lại FULL log (file runner không bị cắt 240k như log in-memory của web_server)
    # để lấy token usage + session id; rollout trong ~/.codex/sessions cho số chính xác hơn.
    usage = None
    session_id = None
    model = None
    tokens_source = "missing"
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        usage = cost_tracking.parse_token_usage(log_text)
        session_id = cost_tracking.parse_session_id(log_text)
        model = cost_tracking.parse_model_line(log_text)
        if usage:
            tokens_source = "stdout"
        rollout = cost_tracking.find_rollout_file(session_id)
        parsed = cost_tracking.parse_rollout(rollout) if rollout else None
        if parsed:
            model = parsed.get("model") or model
            if parsed.get("tokens"):
                usage = parsed["tokens"]
                tokens_source = "rollout"
    except Exception as exc:
        log(f"Không parse được token usage cho job {job_id}: {exc}")

    write_status(job_id, {
        "status": "exited",
        "returncode": returncode,
        "finished_at": time.time(),
        "cancelled": cancelled,
        "usage": usage,
        "session_id": session_id,
        "model": model,
        "tokens_source": tokens_source,
    })
    request_path.unlink(missing_ok=True)
    log(f"Deck job {job_id} kết thúc (returncode {returncode}{', cancelled' if cancelled else ''})")


def cleanup_stale_files(max_age_hours: float = 24.0) -> None:
    if not JOBS_ROOT.is_dir():
        return
    cutoff = time.time() - max_age_hours * 3600
    for path in JOBS_ROOT.iterdir():
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def _graceful_exit(*_args) -> None:
    raise KeyboardInterrupt


def main() -> None:
    # SIGTERM cũng dọn heartbeat như Ctrl+C
    signal.signal(signal.SIGTERM, _graceful_exit)
    if not codex_binary_path():
        print("Không tìm thấy Codex CLI trên host. Cài: npm i -g @openai/codex rồi codex login.")
        sys.exit(1)
    JOBS_ROOT.mkdir(parents=True, exist_ok=True)
    cleanup_stale_files()
    write_heartbeat()
    log(f"Host runner sẵn sàng. Queue: {JOBS_ROOT}")
    log("Web UI trong container sẽ tự nhận runner này (mục 'Tạo slide mới từ link').")
    last_heartbeat = 0.0
    try:
        while True:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                write_heartbeat()
                last_heartbeat = now
            for request_path in sorted(JOBS_ROOT.glob("*.request.json")):
                run_deck_job(request_path)
                last_heartbeat = 0.0
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log("Đã dừng host runner.")
    finally:
        HEARTBEAT_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
