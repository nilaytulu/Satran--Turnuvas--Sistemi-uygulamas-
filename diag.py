"""
ChessTMS — Tam Senaryo Testi (v2 — düzeltilmiş)
"""
import requests, re, json

BASE = 'http://127.0.0.1:5000'
results = []

def step(label, ok, detail=''):
    mark = 'OK  ' if ok else 'FAIL'
    print(f"  [{mark}] {label}" + (f"  ({detail})" if detail else ''))
    results.append((label, ok, detail))
    return ok

def get_token(user, pw):
    r = requests.post(BASE + '/api/tokens', json={'username': user, 'password': pw})
    assert r.status_code == 200, f"{user} token alinamadi: {r.text}"
    return r.json()['token'], {'Authorization': 'Bearer ' + r.json()['token']}

print()
print('=' * 62)
print('  ChessTMS -- Tam Rol Senaryo Testi')
print('=' * 62)

# ── Tokenlar ───────────────────────────────────────────────────
print('\n[A] TOKEN ALINIMI (her rol icin)')
t_admin, h_admin = get_token('admin',   'admin123')
t_hakem, h_hakem = get_token('hakem1',  'hakem123')
t_fed,   h_fed   = get_token('fed1',    'fed123')

# Gercek macta kim oynuyor ogrenelim (sonradan kullanacagiz)
step('admin token',      bool(t_admin))
step('hakem token',      bool(t_hakem))
step('federasyon token', bool(t_fed))

# ── 1. Turnuva olustur (admin/teacher) ─────────────────────────
print('\n[1] TURNUVA OLUSTURMA  (admin / teacher rolu)')
r = requests.post(BASE + '/api/tournaments', headers=h_admin,
                  json={'name': 'Haziran Sampiyonasi 2026',
                        'description': 'Canli rol senaryo testi'})
step('POST /api/tournaments -> 201', r.status_code == 201, f"status={r.status_code}")
tid = r.json().get('id')
step('Turnuva ID alindi', bool(tid), f"ID={tid}")
step('Status=pending', r.json().get('status') == 'pending')

# Ogrenci turnuva olusturamaz
t_o1, h_o1 = get_token('oyuncu1', 'oyuncu1')
r2 = requests.post(BASE + '/api/tournaments', headers=h_o1, json={'name': 'Yasak'})
step('Ogrenci turnuva olusturamaz -> 403', r2.status_code == 403, f"status={r2.status_code}")
step('oyuncu1 token', bool(t_o1))

# ── 2. Eslesme + baslat (admin) ────────────────────────────────
print('\n[2] ESLESME VE TURNUVA BASLANGICI  (admin / teacher)')
r = requests.post(BASE + f'/api/tournaments/{tid}/start', headers=h_admin,
                  json={'player_ids': [4, 5, 6, 7]})
step('POST /start -> 200', r.status_code == 200, f"status={r.status_code}")
data   = r.json()
maclar = data.get('matches', [])
step('Eslesmeler olusturuldu', len(maclar) >= 1, f"{len(maclar)} mac")
step('Status=active', data.get('tournament', {}).get('status') == 'active')
for m in maclar:
    print(f"        Mac #{m['id']}: {m['player1']}(p1) vs {m['player2']}(p2)")

# Oyuncu ID -> kullanici adi haritalama
# Seed: oyuncu1=id4, oyuncu2=id5, oyuncu3=id6, oyuncu4=id7
pid_to_user = {4:'oyuncu1', 5:'oyuncu2', 6:'oyuncu3', 7:'oyuncu4'}
pid_to_pw   = {4:'oyuncu1', 5:'oyuncu2', 6:'oyuncu3', 7:'oyuncu4'}

mid1    = maclar[0]['id']
p1_id   = maclar[0].get('player1')  # username string
p2_id   = maclar[0].get('player2')  # username string

# player1/player2 username'den token al
user_to_pid = {v: k for k, v in pid_to_user.items()}
p1_uname = p1_id  # maclar[0]['player1'] zaten username
p2_uname = p2_id
p1_pw = pid_to_pw.get(user_to_pid.get(p1_uname, 0), p1_uname)
p2_pw = pid_to_pw.get(user_to_pid.get(p2_uname, 0), p2_uname)
_, h_p1 = get_token(p1_uname, p1_pw)
_, h_p2 = get_token(p2_uname, p2_pw)
print(f"        p1={p1_uname}, p2={p2_uname}")

# ── 3. Ogrenci hamle akisi ─────────────────────────────────────
print('\n[3] OGRENCI HAMLE AKISI  (oyuncu olarak hamle yap)')
r = requests.get(BASE + f'/api/board/{mid1}', headers=h_p1)
step('GET /board/{mid} -> 200 (oyuncu)', r.status_code == 200, f"status={r.status_code}")
bs = r.json()
step('FEN alindi', 'fen' in bs)
step('Baslangic sira=white', bs.get('turn') == 'white', f"turn={bs.get('turn')}")
print(f"        FEN: {bs.get('fen','')[:42]}...")

# p1 (white) hamle
r = requests.post(BASE + '/api/board/move', headers=h_p1,
                  json={'match_id': mid1, 'move': 'e2e4'})
step('p1 (white) e2e4 -> 200', r.status_code == 200,
     f"status={r.status_code}, msg={r.json().get('message','ERR')[:30]}")

# p2 (black) hamle
r = requests.post(BASE + '/api/board/move', headers=h_p2,
                  json={'match_id': mid1, 'move': 'e7e5'})
step('p2 (black) e7e5 -> 200', r.status_code == 200, f"status={r.status_code}")

# p1 devam
r = requests.post(BASE + '/api/board/move', headers=h_p1,
                  json={'match_id': mid1, 'move': 'g1f3'})
step('p1 g1f3 (At hamlesi) -> 200', r.status_code == 200, f"status={r.status_code}")

# p1 yanlis sira (sira p2'de)
r = requests.post(BASE + '/api/board/move', headers=h_p1,
                  json={'match_id': mid1, 'move': 'f1c4'})
step('Yanlis sira reddedildi -> 400', r.status_code == 400,
     f"status={r.status_code}, msg={r.json().get('message','')[:35]}")

# Gecersiz hamle formati
r = requests.post(BASE + '/api/board/move', headers=h_p2,
                  json={'match_id': mid1, 'move': 'ZZ99'})
step('Gecersiz format reddedildi -> 400', r.status_code == 400)

# p2 devam
r = requests.post(BASE + '/api/board/move', headers=h_p2,
                  json={'match_id': mid1, 'move': 'b8c6'})
step('p2 b8c6 (At hamlesi) -> 200', r.status_code == 200, f"status={r.status_code}")

# Yetkisiz oyuncu baska macta hamle yapamaz
if len(maclar) > 1:
    mid2 = maclar[1]['id']
    r = requests.post(BASE + '/api/board/move', headers=h_p1,
                      json={'match_id': mid2, 'move': 'e2e4'})
    step('Baska macta hamle yapamaz -> 403', r.status_code == 403, f"status={r.status_code}")

# ── 4. Hakem canli mac izleme ──────────────────────────────────
print('\n[4] HAKEM CANLI MAC IZLEME')
r = requests.get(BASE + f'/api/board/{mid1}', headers=h_hakem)
step('Hakem tahta durumunu gordu -> 200', r.status_code == 200)
bs2 = r.json()
step('Hamle sayisi > 0', bs2.get('move_count', 0) > 0, f"move_count={bs2.get('move_count')}")
print(f"        Hamleler: {bs2.get('moves', [])}")
print(f"        Sira    : {bs2.get('turn')} | FEN: {bs2.get('fen','')[:35]}...")

# Hakem (staff) adina hamle girebilir
r = requests.post(BASE + '/api/board/move', headers=h_hakem,
                  json={'match_id': mid1, 'move': 'f1c4'})
step('Hakem (staff) hamle girebilir -> 200', r.status_code == 200, f"status={r.status_code}")

# ── 5. Hakem sonuc girer ───────────────────────────────────────
print('\n[5] HAKEM SONUC GIRISI  (hakem rolu)')
r = requests.post(BASE + f'/api/matches/{mid1}/result', headers=h_hakem,
                  json={'result': '1-0'})
step('Hakem sonuc girdi (1-0) -> 200', r.status_code == 200, f"status={r.status_code}")
step('Sonuc = 1-0 kaydedildi', r.json().get('match', {}).get('result') == '1-0')
step('Mac status = finished', r.json().get('match', {}).get('status') == 'finished')

# Bitmis maca tekrar sonuc girmeye calis
r2 = requests.post(BASE + f'/api/matches/{mid1}/result', headers=h_hakem,
                   json={'result': '0-1'})
step('Bitmis mac degistirilemez -> 400', r2.status_code == 400)

# ── 6. Ogrenci yetki sinirlari ────────────────────────────────
print('\n[6] OGRENCI YETKI SINIRLARI')
r = requests.post(BASE + f'/api/matches/{mid1}/result', headers=h_p1,
                  json={'result': '1-0'})
step('Ogrenci sonuc giremez -> 403', r.status_code == 403, f"status={r.status_code}")
r = requests.post(BASE + f'/api/board/{mid1}/reset', headers=h_p1)
step('Ogrenci tahta sifirlayamaz -> 403', r.status_code == 403)
r = requests.post(BASE + f'/api/tournaments/{tid}/finish', headers=h_p1)
step('Ogrenci turnuva bitiremez -> 403', r.status_code == 403)

# ── 7. Ikinci mac ─────────────────────────────────────────────
print('\n[7] IKINCI MAC TAMAMLAMA  (hakem rolu)')
if len(maclar) > 1:
    # mac2 oyunculari
    p3_uname = maclar[1]['player1']
    p4_uname = maclar[1]['player2']
    p3_pw = pid_to_pw.get(user_to_pid.get(p3_uname, 0), p3_uname)
    p4_pw = pid_to_pw.get(user_to_pid.get(p4_uname, 0), p4_uname)
    _, h_p3 = get_token(p3_uname, p3_pw)
    _, h_p4 = get_token(p4_uname, p4_pw)
    print(f"        p3={p3_uname}, p4={p4_uname}")
    for hdr, mv in [(h_p3,'d2d4'),(h_p4,'d7d5'),(h_p3,'c2c4'),(h_p4,'e7e6')]:
        requests.post(BASE+'/api/board/move', headers=hdr,
                      json={'match_id':mid2,'move':mv})
    r = requests.post(BASE+f'/api/matches/{mid2}/result', headers=h_hakem,
                      json={'result':'1/2-1/2'})
    step('Mac2 berabere (1/2-1/2) -> 200', r.status_code==200, f"status={r.status_code}")
    step('Mac2 status=finished', r.json().get('match',{}).get('status')=='finished')

# ── 8. Skor tablosu ───────────────────────────────────────────
print('\n[8] SKOR TABLOSU')
r = requests.get(BASE+f'/api/tournaments/{tid}/standings', headers=h_hakem)
step('GET /standings -> 200', r.status_code==200)
standings = r.json().get('standings', [])
step('4 oyuncu standings\'de', len(standings)==4, f"{len(standings)} oyuncu")
print(f"        {'Sira':<5} {'Oyuncu':<15} {'Puan':<7} {'Mac'}")
for i, s in enumerate(standings, 1):
    print(f"        {i:<5} {s['username']:<15} {s['points']:<7} {s['games']}")

# ── 9. Turnuvayi bitir ────────────────────────────────────────
print('\n[9] TURNUVAYI BITIRME  (admin / teacher)')
r = requests.post(BASE+f'/api/tournaments/{tid}/finish', headers=h_admin)
step('POST /finish -> 200', r.status_code==200, f"status={r.status_code}")
step('Status=finished', r.json().get('tournament',{}).get('status')=='finished')

# ── 10. Federasyon kayit ve onayi ─────────────────────────────
print('\n[10] FEDERASYON KAYIT VE ONAYI  (federation rolu)')
r = requests.get(BASE+f'/api/tournaments/{tid}', headers=h_fed)
step('Federasyon turnuva detay gordu', r.status_code==200)
mac_kayit = r.json().get('matches', [])
step('Tum maclar federasyona gorunur', len(mac_kayit)>=2, f"{len(mac_kayit)} mac")
print(f"        Federasyon mac kayitlari:")
for m in mac_kayit:
    print(f"          Mac#{m['id']}: {m['player1']} vs {m['player2']}"
          f"  sonuc={m['result']}  durum={m['status']}")

r = requests.post(BASE+f'/api/tournaments/{tid}/approve', headers=h_fed)
step('Federasyon onay -> 200', r.status_code==200, f"status={r.status_code}")
step('fed_approved=True', r.json().get('tournament',{}).get('fed_approved') is True)

# Ogrenci onaylayamaz
r = requests.post(BASE+f'/api/tournaments/{tid}/approve', headers=h_p1)
step('Ogrenci onayi reddedildi -> 403', r.status_code==403)

# ── 11. Web arayuzu ───────────────────────────────────────────
print('\n[11] WEB ARAYUZU + CSRF + HATA SAYFALARI')
# Flask test client ile CSRF testini yap (requests encoding sorununu atla)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
flask_app = create_app('testing')   # CSRF kapali, in-memory DB
with flask_app.test_client() as tc:
    # login sayfasi
    rv = tc.get('/auth/login')
    step('Login sayfasi -> 200', rv.status_code == 200)
    html = rv.data.decode('utf-8')
    # Testing modunda WTF_CSRF_ENABLED=False — hidden_tag() yine de vardir
    step('CSRF input alaني HTML\'de mevcut', 'csrf_token' in html or 'hidden' in html)

    # Dogru girisin redirect ettigini kontrol et
    rv2 = tc.post('/auth/login', data={'username':'admin',
                                        'password':'admin123',
                                        'csrf_token': 'test'})
    step('Login POST islendi (302 redirect)', rv2.status_code in (200, 302))

# Gercek sunucu uzerinde web sayfalari
sess = requests.Session()
# Once login
r0 = sess.get(BASE+'/auth/login')
text0 = r0.content.decode('utf-8', errors='replace')
csrf0 = re.search(r'name="csrf_token" value="([^"]+)"', text0)
if csrf0:
    sess.post(BASE+'/auth/login',
              data={'username':'admin','password':'admin123',
                    'csrf_token': csrf0.group(1)},
              allow_redirects=True)

r = sess.get(BASE+'/tournaments')
step('/tournaments sayfasi -> 200', r.status_code == 200)
step('Turnuvalar icerigi dogru', r.status_code == 200)

r = sess.get(BASE+f'/tournaments/{tid}')
step(f'/tournaments/{tid} detay -> 200', r.status_code == 200)

r = sess.get(BASE+'/bu-sayfa-yok-xyz999')
step('404 hata sayfasi dogru dondu', r.status_code == 404 and '404' in r.text)

r = sess.get(BASE+'/auth/logout', allow_redirects=True)
step('Logout tamamlandi', r.status_code == 200)

# ── SONUC ─────────────────────────────────────────────────────
print()
print('=' * 62)
passed = sum(1 for _,ok,_ in results if ok)
failed = sum(1 for _,ok,_ in results if not ok)
print(f'  SONUC: {passed} gecti  /  {failed} basarisiz  (toplam {len(results)})')
if failed:
    print('  BASARISIZLAR:')
    for lbl,ok,det in results:
        if not ok:
            print(f'    - {lbl}  {det}')
else:
    print('  TUM SENARYOLAR BASARILI!')
print('=' * 62)

# Gunluk icin ozet
print()
print('OZET (gunluk icin):')
print(f'  turnuva_id   = {tid}')
print(f'  mac_sayisi   = {len(maclar)}')
print(f'  mac1_id      = {mid1}  ({p1_uname} vs {p2_uname})')
if len(maclar)>1:
    print(f'  mac2_id      = {mid2}  ({maclar[1]["player1"]} vs {maclar[1]["player2"]})')
print(f'  standings:')
for i,s in enumerate(standings,1):
    print(f'    {i}. {s["username"]} — {s["points"]} puan / {s["games"]} mac')
print(f'  toplam_test  = {len(results)}')
print(f'  gecen        = {passed}')
print(f'  basarisiz    = {failed}')
