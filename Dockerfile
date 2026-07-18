FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# Shell form so $PORT expands -- Cloud Run injects PORT and expects the
# container to listen on it. --timeout 120 because one /api/analyze makes
# three sequential Gemini calls (~20-60s total); gunicorn's default 30s
# would kill the worker mid-request. Threads > workers: the work is
# IO-bound (waiting on Gemini), not CPU-bound.
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 app:app
