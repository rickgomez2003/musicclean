FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MUSICCLEAN_ORION_DATABASE=/var/lib/musicclean/orion.db \
    MUSICCLEAN_ORION_HOST=0.0.0.0 \
    MUSICCLEAN_ORION_PORT=8765

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir ".[orion-runtime]"

RUN useradd --create-home --uid 10001 musicclean \
    && mkdir -p /var/lib/musicclean /var/log/musicclean \
    && chown -R musicclean:musicclean /var/lib/musicclean /var/log/musicclean /app

USER musicclean

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/v1/health', timeout=3)"

CMD ["python", "-m", "musicclean.orion.runtime"]
