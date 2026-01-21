import os
import time
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BULUNDU_DOSYA = "bulundu.txt"

def telegram_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mesaj
    }
    requests.post(url, data=data)

def tarih_araligi(baslangic, bitis):
    gunler = []
    tarih = baslangic
    while tarih <= bitis:
        gunler.append(tarih.strftime("%Y-%m-%d"))
        tarih += timedelta(days=1)
    return gunler

def bilet_kontrol(tarih):
    url = "https://api.tcddtasimacilik.gov.tr/availability"
    payload = {
        "departureStationId": "ANK",
        "arrivalStationId": "TAT",
        "departureDate": tarih,
        "passengerCount": 4
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()

        for tren in data.get("trains", []):
            for vagon in tren.get("wagons", []):
                ad = vagon.get("name", "").lower()
                bos = vagon.get("availableSeatCount", 0)

                if bos >= 4 and ("kuşet" in ad or "yatak" in ad):
                    return tren.get("trainNumber"), tarih, vagon.get("name")

    except Exception:
        pass

    return None

if name == "main":
    if os.path.exists(BULUNDU_DOSYA):
        exit()

    baslangic = datetime(2026, 1, 22)
    bitis = datetime(2026, 2, 3)

    telegram_mesaj("🚆 TCDD bilet botu çalışıyor, kontrol ediyorum...")

    while True:
        for tarih in tarih_araligi(baslangic, bitis):
            sonuc = bilet_kontrol(tarih)
            if sonuc:
                tren, gun, vagon = sonuc
                mesaj = (
                    "🎉 BİLET BULUNDU!\n\n"
                    f"📍 Ankara → Tatvan\n"
                    f"📅 Tarih: {gun}\n"
                    f"🚆 Tren: {tren}\n"
                    f"🛏️ Vagon: {vagon}\n"
                    f"👥 Kişi: 4"
                )
                telegram_mesaj(mesaj)
                with open(BULUNDU_DOSYA, "w") as f:
                    f.write("bulundu")
                exit()

        time.sleep(300)
