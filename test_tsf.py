"""
TSF Son 6 Ay Verisi ile Kapsamlı Sistem Testi
============================================
Gercek TSF turnuva ve oyuncu isimleri kullanilarak (Nov 2024 - May 2025)
tum API endpoint'leri test edilir ve degerlendirilir.
"""

import requests
import json
import sys
from datetime import datetime

BASE = "http://127.0.0.1:5000/api"
RESULTS = []

def log(msg, status="INFO"):
    symbols = {"OK": "[OK]", "FAIL": "[FAIL]", "INFO": "[..]", "WARN": "[!!]"}
    print(f"{symbols.get(status, '[..]')} {msg}")
    RESULTS.append({"status": status, "msg": msg})

def test(name, r, expected_status=200):
    if r.status_code == expected_status:
        log(f"{name} -> HTTP {r.status_code}", "OK")
        return r.json()
    else:
        log(f"{name} -> HTTP {r.status_code} (beklenen {expected_status}) | {r.text[:120]}", "FAIL")
        return None

# ─────────────────────────────────────────────
# 1. TOKEN ALMA - Farkli roller
# ─────────────────────────────────────────────
log("=" * 60)
log("BOLUM 1: Kimlik Dogrulama Testleri")
log("=" * 60)

users = {
    "admin":   ("admin",   "admin123"),
    "hakem1":  ("hakem1",  "hakem123"),
    "fed1":    ("fed1",    "fed123"),
    "oyuncu1": ("oyuncu1", "oyuncu1"),
    "oyuncu2": ("oyuncu2", "oyuncu2"),
    "oyuncu3": ("oyuncu3", "oyuncu3"),
    "oyuncu4": ("oyuncu4", "oyuncu4"),
}

tokens = {}
user_ids = {}

for key, (uname, pwd) in users.items():
    r = requests.post(f"{BASE}/tokens", json={"username": uname, "password": pwd})
    data = test(f"Login: {uname}", r)
    if data:
        tokens[key] = data["token"]
        user_ids[key] = data["user"]["id"]

# Hatali giris testi
r = requests.post(f"{BASE}/tokens", json={"username": "admin", "password": "yanlis"})
if r.status_code == 401:
    log("Yanlis sifre ile giris reddedildi (401)", "OK")
else:
    log(f"Yanlis sifre ile giris: Beklenmeyen HTTP {r.status_code}", "FAIL")

admin_h = {"Authorization": f"Bearer {tokens['admin']}"}
hakem_h = {"Authorization": f"Bearer {tokens['hakem1']}"}
fed_h   = {"Authorization": f"Bearer {tokens['fed1']}"}

# ─────────────────────────────────────────────
# 2. KULLANICI TESTLERI
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 2: Kullanici Yonetimi")
log("=" * 60)

# Kullanici listesi
r = requests.get(f"{BASE}/users", headers=admin_h)
data = test("Tum kullanicilari listele (admin)", r)
if data:
    log(f"  Sistemde {data['total']} kullanici mevcut")

# TSF benzeri yeni oyuncular olustur (Son 6 ayin gercek Turk satranc oyunculari)
tsf_players = [
    {"username": "vahap_sanal",   "email": "vahap@chess.tr",   "password": "sifre123", "role": "student"},
    {"username": "isik_can",      "email": "isik@chess.tr",    "password": "sifre123", "role": "student"},
    {"username": "yagiz_erdogmus","email": "yagiz@chess.tr",   "password": "sifre123", "role": "student"},
    {"username": "emre_can",      "email": "emrecan@chess.tr", "password": "sifre123", "role": "student"},
    {"username": "suat_atalik",   "email": "suat@chess.tr",    "password": "sifre123", "role": "student"},
    {"username": "mustafa_yilmaz","email": "mustafa@chess.tr", "password": "sifre123", "role": "student"},
    {"username": "ali_marandi",   "email": "ali@chess.tr",     "password": "sifre123", "role": "student"},
    {"username": "buse_kalkan",   "email": "buse@chess.tr",    "password": "sifre123", "role": "student"},
]

new_player_ids = []
for p in tsf_players:
    r = requests.post(f"{BASE}/users", json=p, headers=admin_h)
    if r.status_code == 201:
        pid = r.json()["id"]
        new_player_ids.append(pid)
        log(f"  Oyuncu olusturuldu: {p['username']} (id={pid})", "OK")
    elif r.status_code == 400 and "zaten" in r.text:
        # Zaten var, ID'yi bul
        r2 = requests.get(f"{BASE}/users", headers=admin_h)
        for u in r2.json().get("items", []):
            if u["username"] == p["username"]:
                new_player_ids.append(u["id"])
                log(f"  Oyuncu zaten var: {p['username']} (id={u['id']})", "WARN")
                break
    else:
        log(f"  Oyuncu olusturulamadi: {p['username']} -> {r.status_code}", "FAIL")

# Yetkisiz kullanici olusturma (oyuncu rolundekinden)
p4_h = {"Authorization": f"Bearer {tokens['oyuncu1']}"}
r = requests.post(f"{BASE}/users", json={"username": "test", "email": "t@t.com", "password": "x"}, headers=p4_h)
if r.status_code == 403:
    log("Oyuncu kullanici olusturamaz (403 Forbidden)", "OK")
else:
    log(f"Rol kontrolu basarisiz: {r.status_code}", "FAIL")

# ─────────────────────────────────────────────
# 3. TURNUVA TESTLERI (Son 6 ay TSF Turnuvalari)
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 3: TSF Son 6 Ay Turnuvalari")
log("=" * 60)

tsf_tournaments = [
    {
        "name": "2024 Turkiye Satranc Sampiyonasi",
        "description": "12-23 Aralik 2024, Ankara. Sampiyon: GM Vahap Sanal"
    },
    {
        "name": "2025 Turkiye Gencler Satranc Sampiyonasi",
        "description": "Ocak 2025, Yesilim Turizm sponsorlugunda"
    },
    {
        "name": "2025 Turkiye Hizli ve Yildirim Satranc Sampiyonasi",
        "description": "Subat 2025, Ankara. Yildiz: Isik Can"
    },
    {
        "name": "2025 Baku Acik Satranc Festivali",
        "description": "Mayis 2026. Turkiye temsilcisi: Yagiz Kaan Erdogmus"
    },
]

tournament_ids = []
for t in tsf_tournaments:
    r = requests.post(f"{BASE}/tournaments", json=t, headers=admin_h)
    data = test(f"Turnuva olustur: {t['name'][:40]}...", r, 201)
    if data:
        tournament_ids.append(data["id"])
        log(f"  -> Turnuva ID: {data['id']}")

# Turnuva listesi
r = requests.get(f"{BASE}/tournaments", headers=admin_h)
data = test("Turnuva listesi", r)
if data:
    log(f"  Sistemde toplam {data['total']} turnuva var")

# ─────────────────────────────────────────────
# 4. TURNUVA BASLATMA (Oyuncu eslesmesi)
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 4: Turnuva Baslatma ve Eslesmeler")
log("=" * 60)

all_player_ids = list(user_ids.values())[3:]  # oyuncu1-4
all_player_ids += new_player_ids[:4]           # TSF oyuncularindan 4'u

active_tid = None
if tournament_ids:
    active_tid = tournament_ids[0]
    r = requests.post(
        f"{BASE}/tournaments/{active_tid}/start",
        json={"player_ids": all_player_ids},
        headers=admin_h
    )
    data = test(f"Turnuva baslatma (ID={active_tid})", r)
    if data:
        log(f"  {data.get('message', '')}", "OK")
        matches_created = data.get("matches", [])
        log(f"  {len(matches_created)} mac olusturuldu")

# Zaten baslatilmis turnuvaya baslatma denemesi
if active_tid:
    r = requests.post(
        f"{BASE}/tournaments/{active_tid}/start",
        json={"player_ids": all_player_ids},
        headers=admin_h
    )
    if r.status_code == 400:
        log("Zaten aktif turnuvaya baslatma istegi reddedildi (400)", "OK")

# ─────────────────────────────────────────────
# 5. MAC SONUCLARI GIRME
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 5: Mac Sonuclari (Hakem girisli)")
log("=" * 60)

# TSF benzeri gercek mac sonuclari
tsf_results = [
    ("1-0",     "Beyaz galip - TSF standart sonuc"),
    ("0-1",     "Siyah galip - TSF standart sonuc"),
    ("1/2-1/2", "Beraberlik - TSF standart sonuc"),
    ("1-0",     "Beyaz galip"),
]

# Turnuva maclarini al
match_ids = []
if active_tid:
    r = requests.get(f"{BASE}/tournaments/{active_tid}", headers=admin_h)
    data = test(f"Turnuva detayi (ID={active_tid})", r)
    if data:
        match_ids = [m["id"] for m in data.get("matches", [])]
        log(f"  {len(match_ids)} mac bulundu")

# Mac sonuclarini gir
# NOT: Bu bolum tum maclari aninda tamamlar.
# Gercek oyun akisinda once hamleler girilmeli (POST /api/board/move),
# ardindan hakem sonucu girmeli (POST /api/matches/<id>/result).
for i, mid in enumerate(match_ids):
    result, desc = tsf_results[i % len(tsf_results)]
    r = requests.post(
        f"{BASE}/matches/{mid}/result",
        json={"result": result},
        headers=hakem_h
    )
    if r.status_code == 400 and "zaten tamamlanmış" in r.text:
        log(f"  Mac {mid} zaten tamamlanmis, atlaniyor", "WARN")
    else:
        data = test(f"  Mac {mid} sonucu: {result} ({desc})", r)

# Oyuncunun sonuc girmeye calismasi (yetkisiz)
if match_ids:
    r = requests.post(
        f"{BASE}/matches/{match_ids[0]}/result",
        json={"result": "1-0"},
        headers=p4_h
    )
    if r.status_code == 403:
        log("Oyuncu mac sonucu giremez (403 Forbidden)", "OK")

# Gecersiz sonuc
if match_ids:
    r = requests.post(
        f"{BASE}/matches/{match_ids[0]}/result",
        json={"result": "2-0"},
        headers=hakem_h
    )
    if r.status_code == 400:
        log("Gecersiz sonuc reddedildi (400)", "OK")

# ─────────────────────────────────────────────
# 6. SKOR TABLOSU
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 6: Puan Tablosu (TSF Standart Siralama)")
log("=" * 60)

if active_tid:
    r = requests.get(f"{BASE}/tournaments/{active_tid}/standings", headers=admin_h)
    data = test(f"Puan tablosu (Turnuva ID={active_tid})", r)
    if data:
        log(f"  Turnuva: {data.get('tournament')}")
        standings = data.get("standings", [])
        for i, s in enumerate(standings[:8], 1):
            log(f"  {i:2}. {s['username']:<20} {s['points']:.1f} puan  ({s['games']} mac)")

# ─────────────────────────────────────────────
# 7. TURNUVAYI TAMAMLAMA
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 7: Turnuva Tamamlama ve Federasyon Onayi")
log("=" * 60)

if active_tid:
    r = requests.post(f"{BASE}/tournaments/{active_tid}/finish", headers=hakem_h)
    data = test("Turnuvayi tamamla (hakem)", r)
    if data:
        log(f"  Durum: {data.get('tournament', {}).get('status')}", "OK")

    # Federasyon onayi
    r = requests.post(f"{BASE}/tournaments/{active_tid}/approve", headers=fed_h)
    data = test("Federasyon onayi", r)
    if data:
        log(f"  fed_approved: {data.get('tournament', {}).get('fed_approved')}", "OK")

    # Tamamlanmamis turnuvaya onay denemesi
    if len(tournament_ids) > 1:
        r = requests.post(f"{BASE}/tournaments/{tournament_ids[1]}/approve", headers=fed_h)
        if r.status_code == 400:
            log("Tamamlanmamis turnuvaya onay reddedildi (400)", "OK")

# ─────────────────────────────────────────────
# 8. TOKEN IPTAL TESTLERI
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("BOLUM 8: Token Guvenligi")
log("=" * 60)

# Token iptal et
r = requests.delete(f"{BASE}/tokens", headers=hakem_h)
test("Token iptal (hakem1 logout)", r)

# Iptal edilmis token ile istek
r = requests.get(f"{BASE}/users", headers=hakem_h)
if r.status_code == 401:
    log("Iptal edilmis token ile erisim reddedildi (401)", "OK")
else:
    log(f"Token iptal kontrolu basarisiz: {r.status_code}", "FAIL")

# Tokensiz istek
r = requests.get(f"{BASE}/users")
if r.status_code == 401:
    log("Tokensiz erisim reddedildi (401)", "OK")

# ─────────────────────────────────────────────
# SONUC RAPORU
# ─────────────────────────────────────────────
log("")
log("=" * 60)
log("SONUC RAPORU")
log("=" * 60)

ok   = sum(1 for r in RESULTS if r["status"] == "OK")
fail = sum(1 for r in RESULTS if r["status"] == "FAIL")
warn = sum(1 for r in RESULTS if r["status"] == "WARN")
total = ok + fail

log(f"Toplam Test : {total}")
log(f"Basarili    : {ok}  ({ok/max(total,1)*100:.0f}%)")
log(f"Basarisiz   : {fail}")
log(f"Uyari       : {warn}")
log("")

if fail == 0:
    log("TUMU GECTI - Sistem TSF standartlariyla calisyor!", "OK")
else:
    log(f"{fail} TEST BASARISIZ - Asagida listelenenleri kontrol edin:", "FAIL")
    for r in RESULTS:
        if r["status"] == "FAIL":
            log(f"  -> {r['msg']}", "FAIL")

sys.exit(0 if fail == 0 else 1)
