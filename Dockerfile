FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    DISPLAY=:99 \
    XVFB_SCREEN=1400x2200x24

# ffmpeg/ffprobe cho render, xvfb cho tab capture (auto_render.py chạy Chromium headful),
# pulseaudio làm audio sink giả để MediaRecorder trong trang có sample,
# fonts-noto cho tiếng Việt và emoji trên slide.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        xvfb \
        x11-utils \
        pulseaudio \
        pulseaudio-utils \
        fonts-noto-core \
        fonts-noto-cjk \
        fonts-noto-color-emoji \
        fonts-dejavu-core \
        ca-certificates \
        curl \
        gnupg \
        procps \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Node 20 + bird cho workflow X/Twitter (không bắt buộc, build vẫn qua nếu fail)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && (npm install -g @steipete/bird || echo "bird install skipped")

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt \
    && python -m pip install "yt-dlp[default]" \
    && python -m playwright install --with-deps chromium \
    && chmod -R a+rX /opt/playwright

RUN useradd --create-home --uid 1000 ntc

WORKDIR /app
COPY --chown=ntc:ntc . /app
COPY --chown=root:root docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod 755 /usr/local/bin/entrypoint.sh

# Để docker exec và mọi subprocess thấy cùng socket pulseaudio với entrypoint
ENV XDG_RUNTIME_DIR=/tmp/runtime-ntc

USER ntc
EXPOSE 8765

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["python", "web_server.py"]
