FROM python:3.11-slim as builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY main.py workload_generator.py metrics_simulator.py ./

ENV PYTHONUNBUFFERED=1
ENV METRICS_PORT=8001
ENV GENERATION_INTERVAL=60
ENV GENERATE_HISTORICAL=true
ENV HISTORICAL_DAYS=7

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/metrics')" || exit 1

CMD ["python", "-u", "main.py"]
