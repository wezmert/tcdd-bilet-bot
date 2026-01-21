import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))

def telegram_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj}
    requests.post(url, data=data, timeout=10)

def telegram_komut_kontrol():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    r = requests.get(url, timeout=10).json()
    for upd in r.get("result", []):
        msg = upd.get("message", {})
        if not msg: continue
        if msg["chat"]["id"] != CHAT_ID: continue
        text = msg.get("text", "").lower()
        if "çalışıyor" in text or "calisiyor" in text:
            telegram_mesaj("🤖 Evet, buradayım. Bot çalışıyor ve bilet arıyorum.")
            return

def tarih_araligi(baslangic, bitis):
    gunler = []
    t = baslangic
    while t <= bitis:
        gunler.append(t.strftime("%d.%m.%Y"))
        t += timedelta(days=1)
    return gunler

def bilet_kontrol(tarih):
    url = "https://ebilet.tcddtasimacilik.gov.tr/view/available-trains"  # TCDD resmi bilet sayfası
    params = {
        "nereden": "ANK",    # Ankara
        "nereye": "TAT",     # Tatvan
        "tarih": tarih,
        "yolcu": "4"
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    # Bu örnek HTML parsing, sayfa değişirse güncellemek gerekir
    trenler = soup.find_all("div", class_="train-card")
    for tren in trenler:
        numara = tren.find("span", class_="train-number").text.strip()
        vagonlar = tren.find_all("div", class_="wagon")
        for vagon in vagonlar:
            ad = vagon.find("span", class_="wagon-type").text.lower()
            bos = int(vagon.find("span", class_="available-seats").text.strip())
            if bos >= 4 and ("kuşet" in ad or "kuset" in ad or "yatak" in ad):
                return numara, tarih, ad
    return None

if name == "main":
    telegram_komut_kontrol()

    bugun = datetime.now().strftime("%Y-%m-%d")
    dosya = "gunluk.txt"
    if not os.path.exists(dosya) or open(dosya).read().strip() != bugun:
        telegram_mesaj("✅ Bot çalışıyor, bilet kontrolü devam ediyor.")
        open(dosya, "w").write(bugun)

    if os.path.exists("bulundu.txt"):
        exit()

    baslangic = datetime(2026, 1, 22)
    bitis = datetime(2026, 2, 3)

    for tarih in tarih_araligi(baslangic, bitis):
        try:
            sonuc = bilet_kontrol(tarih)
            if sonuc:
                tren, gun, vagon = sonuc
                telegram_mesaj(
                    f"🎉 BİLET BULUNDU!\n\n📍 Ankara → Tatvan\n📅 Tarih: {gun}\n🚆 Tren: {tren}\n🛏️ Vagon: {vagon}\n👥 Kişi: 4"
                )
                open("bulundu.txt", "w").write("ok")
                break
        except Exception:
            telegram_mesaj("⚠️ Bot hata aldı! TCDD HTML yapısı değişmiş olabilir.")
            break
