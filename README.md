# ♟ Satranç Turnuva Yönetim Sistemi

## 1. Projenin Amacı ve Özeti

Bu proje, Gazi Üniversitesi BLG106 İnternet Programcılığı dersi final ödevi kapsamında geliştirilmiş bir **Satranç Turnuva Yönetim Sistemi (ChessTMS)**'dir.

Sistem; turnuva oluşturma, oyuncu eşleştirme, maç sonucu girişi, skor tablosu ve federasyon onay akışlarını yönetir. Dört kullanıcı rolü desteklenir: **Öğrenci/Oyuncu**, **Hakem**, **Federasyon** ve **Öğretmen/Admin**. Ek olarak FEN tabanlı akıllı tahta simülasyonu ve Bearer token destekli REST API içerir.

---

## 2. Kurulum Adımları

```bash
# 1. Depoyu klonla
git clone <repo-url>
cd chess_tournament

# 2. Sanal ortam oluştur ve etkinleştir
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Ortam değişkenlerini ayarla
cp .env.example .env
# .env dosyasını açıp SECRET_KEY değerini düzenle

# 5. Veritabanını oluştur
flask db init      # Sadece ilk kurulumda (migrations/ yoksa)
flask db migrate -m "ilk kurulum"
flask db upgrade
```

---

## 3. Geliştirme ve Çalıştırma Komutları

```bash
# Geliştirme sunucusunu başlat
flask run

# veya doğrudan
python run_py.py

# Testleri çalıştır
pytest -v

# Test kapsam raporu
pytest --cov=app tests/
```

Uygulama varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır.

---

## 4. Kullanılan Teknolojiler

| Teknoloji | Versiyon | Rol |
|---|---|---|
| Python | 3.11+ | Programlama dili |
| Flask | 3.1.3 | Web framework |
| SQLAlchemy | 2.0.49 | ORM (Mapped / mapped_column stili) |
| Flask-SQLAlchemy | 3.1.1 | Flask–SQLAlchemy entegrasyonu |
| Flask-Migrate | 4.1.0 | Alembic tabanlı veritabanı migrasyonu |
| Flask-Login | 0.6.3 | Oturum tabanlı kimlik doğrulama |
| Flask-WTF | 1.3.0 | Form yönetimi ve CSRF koruması |
| Werkzeug | 3.1.8 | Şifre hashleme (`generate_password_hash`) |
| email-validator | 2.3.0 | E-posta adresi doğrulama |
| pytest + pytest-flask | 9.0.3 | Otomatik test altyapısı |

---

## 5. Canlı Dağıtım ve Demo

| | Bağlantı |
|---|---|
| 🌐 **Canlı Uygulama (Render/Railway)** | |
| 🎬 **Demo Videosu** |https://www.youtube.com/shorts/VmF2dnuc5VU|
