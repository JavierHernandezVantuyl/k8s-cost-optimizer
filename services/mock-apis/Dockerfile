FROM python:3.11-slim as builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY main.py models.py pricing_data.py ./

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
