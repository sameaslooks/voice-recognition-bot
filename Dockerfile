FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DB_PATH=/data/bot.db \
    MODEL_DIR=/models

ARG APT_MIRROR=deb.debian.org
RUN sed -i "s|http://deb.debian.org|http://${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources || \
    sed -i "s|http://deb.debian.org|http://${APT_MIRROR}|g" /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

ARG PIP_INDEX_URL=https://pypi.org/simple

RUN pip install --no-cache-dir \
    --index-url ${PIP_INDEX_URL} \
    --timeout 300 \
    --retries 10 \
    -r requirements.txt

COPY bot ./bot

RUN mkdir -p /data /models

CMD ["python", "-m", "bot"]