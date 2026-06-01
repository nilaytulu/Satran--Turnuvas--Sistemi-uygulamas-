# ─────────────────────────────────────────────────────────────
#  ChessTMS — Dockerfile
#  Flask 3.x + SQLAlchemy 2.x
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Bağımlılıkları önce kopyala (layer cache optimizasyonu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Instance dizini oluştur (SQLite DB için)
RUN mkdir -p instance

# Environment değişkenleri
ENV FLASK_APP=run_py.py
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Port
EXPOSE 5000

# Başlatma komutu
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
