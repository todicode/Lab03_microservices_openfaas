FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home app
COPY services ./services
COPY runtime ./runtime
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
USER app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=4s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"
CMD ["python", "runtime/server.py"]

