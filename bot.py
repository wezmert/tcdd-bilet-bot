import os
import requests
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
        if not msg:
            continue
        if msg["chat"]["id"] != CHAT_ID:
            continue

        text = msg.get("text", "").lower()
        if "çalışıyor" in text or "calisiyor" in text:
            telegram_mesaj("🤖 Evet, buradayım. Bot çalışıyor ve bilet arıyorum.")
            return

def tarih_araligi(baslangic, bitis):
    gunler = []
    t = baslangic
    while t <= bitis:
        gunler.append(t.strftime("%Y-%m-%d"))
        t += timedelta(days=1)
    return gunler

def bilet_kontrol(tarih):
    url = "https://api.tcddtasimacilik.gov.tr/availability"
    payload = {
        "departureStationId": "ANK",
        "arrivalStationId": "TAT",
        "departureDate": tarih,
        "passengerCount": 4
    }

    r = requests.post(url, json=payload, timeout=15)
    data = r.json()

    for tren in data.get("trains", []):
        for vagon in tren.get("wagons", []):
            ad = vagon.get("name", "").lower()
            bos = vagon.get("availableSeatCount", 0)

            if bos >= 4 and ("kuşet" in ad or "kuset" in ad or "yatak" in ad):
                return tren.get("trainNumber"), tarih, vagon.get("name")

    return None

if name == "main":
    # Telegram komutuna cevap ver
    telegram_komut_kontrol()

    # Günlük çalışıyor mesajı (günde 1 kez)
    bugun = datetime.now().strftime("%Y-%m-%d")
    dosya = "gunluk.txt"
    if not os.path.exists(dosya) or open(dosya).read().strip() != bugun:
        telegram_mesaj("✅ Bot çalışıyor, bilet kontrolü devam ediyor.")
        open(dosya, "w").write(bugun)

    # Bilet bulunduysa tekrar bakma
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
                    "🎉 BİLET BULUNDU!\n\n"
                    "📍 Ankara → Tatvan\n"
                    f"📅 Tarih: {gun}\n"
                    f"🚆 Tren: {tren}\n"
                    f"🛏️ Vagon: {vagon}\n"
                    "👥 Kişi: 4"
                )
                open("bulundu.txt", "w").write("ok")
                break
        except Exception:
            telegram_mesaj("⚠️ Bot hata aldı! TCDD sistemi değişmiş olabilir.")
            break
