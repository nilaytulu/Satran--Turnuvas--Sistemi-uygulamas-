import requests
import re
import sys

BASE = 'http://127.0.0.1:5000'
s = requests.Session()
errors = []

def check(label, condition, note=""):
    if condition:
        print(f"  OK  {label}" + (f" ({note})" if note else ""))
    else:
        print(f"  FAIL {label}" + (f" ({note})" if note else ""))
        errors.append(label)

print("=" * 55)
print("  ChessTMS -- Canli Smoke Test")
print("=" * 55)

# 1. Ana sayfa login'e yonlendirmeli
print("\n[1] Ana sayfa redirect")
r = s.get(BASE + '/', allow_redirects=False)
check("GET / -> 302 redirect", r.status_code == 302, f"status={r.status_code}")

# 2. Login sayfasi ve CSRF
print("\n[2] Login sayfasi + CSRF token")
r = s.get(BASE + '/auth/login')
check("GET /auth/login -> 200", r.status_code == 200, f"status={r.status_code}")
has_csrf = 'csrf_token' in r.text
check("CSRF token HTML'de mevcut", has_csrf)

# 3. Register sayfasi
print("\n[3] Register sayfasi")
r = s.get(BASE + '/auth/register')
check("GET /auth/register -> 200", r.status_code == 200, f"status={r.status_code}")

# 4. 404 hata sayfasi
print("\n[4] 404 hata sayfasi")
r = s.get(BASE + '/bu-sayfa-yok-xyzabc123')
check("GET /bozuk-url -> 404", r.status_code == 404, f"status={r.status_code}")
check("404 sayfasi icerigi dogru", '404' in r.text)

# 5. 403 hata sayfasi - login gerektiren sayfaya yetkisiz erisim
print("\n[5] Login korumasi (403/302)")
r = s.get(BASE + '/tournaments', allow_redirects=False)
check("Giris yapilmadan /tournaments -> redirect", r.status_code in (302, 403), f"status={r.status_code}")

# 6. API Token alma
print("\n[6] REST API - Token")
r = s.post(BASE + '/api/tokens', json={'username': 'admin', 'password': 'admin123'})
check("POST /api/tokens -> 200", r.status_code == 200, f"status={r.status_code}")
token = r.json().get('token', '')
check("Token donduruldu", bool(token), f"token={token[:12]}..." if token else "bos")

headers = {'Authorization': f'Bearer {token}'}

# 7. Kullanici listesi API
print("\n[7] REST API - Kullanici listesi")
r = s.get(BASE + '/api/users', headers=headers)
check("GET /api/users -> 200", r.status_code == 200, f"status={r.status_code}")
users = r.json().get('users', [])
check("En az 7 kullanici var", len(users) >= 7, f"sayi={len(users)}")
user_names = [u['username'] for u in users]
print(f"       Kullanicilar: {user_names}")

# 7b. Sifre guvenligi: API yaniti password_hash icermemeli
u1 = r.json()['users'][0]
check("API yaniti password_hash icermiyor (gizli)", 'password_hash' not in u1)

# 8. Turnuva listesi API
print("\n[8] REST API - Turnuvalar")
r = s.get(BASE + '/api/tournaments', headers=headers)
check("GET /api/tournaments -> 200", r.status_code == 200, f"status={r.status_code}")
tournaments = r.json().get('tournaments', [])
print(f"       Mevcut turnuva: {len(tournaments)}")

# 9. Yanlis sifre ile token reddedilmeli
print("\n[9] Hatali kimlik bilgisi reddi")
r = s.post(BASE + '/api/tokens', json={'username': 'admin', 'password': 'YANLIS'})
check("Hatali sifre -> 401", r.status_code == 401, f"status={r.status_code}")

# 10. Yetkisiz API erisimi
print("\n[10] API yetki kontrolu")
r = s.get(BASE + '/api/users')
check("Token olmadan /api/users -> 401", r.status_code == 401, f"status={r.status_code}")

# 11. Web giris akisi (CSRF ile POST)
print("\n[11] Web - Gercek login akisi")
r = s.get(BASE + '/auth/login')
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
csrf_val = csrf_match.group(1) if csrf_match else ''
check("Login sayfasindan CSRF alindi", bool(csrf_val))

r2 = s.post(BASE + '/auth/login', data={
    'username': 'admin',
    'password': 'admin123',
    'csrf_token': csrf_val,
    'remember_me': False
}, allow_redirects=True)
check("Login POST -> 200", r2.status_code == 200, f"status={r2.status_code}")
dashboard_ok = ('Kontrol Paneli' in r2.text or 'ChessTMS' in r2.text or
                'chess' in r2.url.lower() or r2.url == BASE + '/')
check("Dashboard'a yonlendirildi", dashboard_ok, f"url={r2.url}")

# 12. Giris sonrasi turnuva sayfasi + pagination HTML
print("\n[12] Web - Turnuvalar sayfasi + Pagination")
r = s.get(BASE + '/tournaments')
check("GET /tournaments -> 200 (giris sonrasi)", r.status_code == 200, f"status={r.status_code}")
pagination_ok = 'page-btn' in r.text or 'pagination' in r.text or 'Turnuvalar' in r.text
check("Turnuvalar sayfasi icerigi dogru", pagination_ok)

# 13. Yeni turnuva olustur (API)
print("\n[13] REST API - Turnuva olustur + lifecycle")
r = s.post(BASE + '/api/tournaments', headers=headers,
           json={'name': 'Smoke Test Turnuvasi', 'description': 'Otomatik test'})
check("POST /api/tournaments -> 201", r.status_code == 201, f"status={r.status_code}")
if r.status_code == 201:
    tid = r.json().get('id')
    print(f"       Olusturulan turnuva ID: {tid}")

    # Detay al
    r2 = s.get(BASE + f'/api/tournaments/{tid}', headers=headers)
    check(f"GET /api/tournaments/{tid} -> 200", r2.status_code == 200)

# 14. Logout
print("\n[14] Web - Logout")
r = s.get(BASE + '/auth/logout', allow_redirects=True)
check("Logout basarili -> 200", r.status_code == 200, f"status={r.status_code}")
check("Login sayfasina yonlendirildi", 'auth/login' in r.url or 'Giris' in r.text or 'Giriş' in r.text)

# SONUC
print()
print("=" * 55)
if errors:
    print(f"BASARISIZ: {len(errors)} test hatalı")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"TUM TESTLER GECTI  (14 kontrol, 0 hata)")
print("=" * 55)
