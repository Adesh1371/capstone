# ── Base image ──────────────────────────────────────────────
FROM python:3.11-slim

# ── Set working directory ────────────────────────────────────
WORKDIR /app

# ── Install system deps (for psycopg2, etc.) ─────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Copy and install Python dependencies ─────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── Copy application code ─────────────────────────────────────
COPY backend/     ./backend/
COPY main.py      .
COPY database.py  .
COPY .env         .

# ── Expose port ───────────────────────────────────────────────
EXPOSE 8000

# ── Start the app with uvicorn ────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
