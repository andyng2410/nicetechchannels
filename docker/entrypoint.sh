#!/usr/bin/env bash
set -euo pipefail

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-ntc}"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

# auto_render.py quay video bằng tab capture với Chromium headful (headless=False)
# và --window-size=1200,2000, nên cần màn hình ảo lớn hơn kích thước cửa sổ,
# nếu không video sẽ bị crop phần dưới.
if ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    # docker restart giữ nguyên /tmp nên lock/socket của Xvfb cũ còn sót lại,
    # Xvfb mới sẽ từ chối start ("Server is already active") nếu không dọn trước.
    display_num="${DISPLAY#:}"
    rm -f "/tmp/.X${display_num}-lock" "/tmp/.X11-unix/X${display_num}"
    Xvfb "$DISPLAY" -screen 0 "$XVFB_SCREEN" -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
    for _ in $(seq 1 60); do
        if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
            break
        fi
        sleep 0.25
    done
fi

if ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    echo "❌ Xvfb không khởi động được trên $DISPLAY, render video sẽ fail." >&2
    cat /tmp/xvfb.log >&2 || true
fi

# Sink âm thanh giả: Chromium cần một output device để AudioContext chạy,
# nếu không __stopSlideAudioRecording() trả rỗng và render báo
# "Browser did not capture slide audio".
if ! pactl info >/dev/null 2>&1; then
    pulseaudio --start --exit-idle-time=-1 --disable-shm \
        -L "module-null-sink sink_name=ntc_dummy sink_properties=device.description=ntc_dummy" \
        >/tmp/pulseaudio.log 2>&1 || echo "⚠️  pulseaudio không start được, xem /tmp/pulseaudio.log" >&2
fi

exec "$@"
