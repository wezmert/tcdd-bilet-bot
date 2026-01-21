import os
import time
import json
import requests
from datetime import datetime, timedelta

# Telegram bilgileri (GitHub Secrets'tan gelir)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Kontrol dosyaları
BULUNDU_DOSYA = "bulundu.txt"
HATA_DOSYA = "hata.txt"
DURUM_DOSYA = "durum.json"


def telegram_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mesaj
    }
    requests.post(url, data=data)


def durum_yukle():
    if os.path.exists(DURUM_DOSYA):
        with open(DURUM_DOSYA, "r") as f:
            return json.load(f)
    return {}


def durum_kaydet(durum):
    with open(DURUM_DOSYA, "w") as f:
        json.dump(durum, f)


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

    r = requests.post(url, json=payload, timeout=15)
    data = r.json()

    for tren in data.get("trains", []):
        for vagon in tren.get("wagons", []):
            ad = vagon.get("name", "").lower()
            bos = vagon.get("availableSeatCount", 0)

            if bos >= 4 and ("kuşet" in ad or "yatak" in ad):
                return tren.get("trainNumber"), tarih, vagon.get("name")

    return None


if name == "main":

    # Eğer bilet bulunduysa tamamen dur
    if os.path.exists(BULUNDU_DOSYA):
        exit()

    durum = durum_yukle()
    bugun = datetime.now().strftime("%Y-%m-%d")

    # İlk çalışma mesajı (1 kere)
    if not durum.get("basladi"):
        telegram_mesaj("🤖 TCDD bilet botu aktif. Kontroller başladı.")
        durum["basladi"] = True

    # Günlük sağlık mesajı (günde 1 kere)
    if durum.get("son_gunluk_mesaj") != bugun:
        telegram_mesaj("✅ Bot çalışıyor, hâlâ bilet arıyorum.")
        durum["son_gunluk_mesaj"] = bugun

    durum_kaydet(durum)

    baslangic = datetime(2026, 1, 22)
    bitis = datetime(2026, 2, 3)

    while True:
        for tarih in tarih_araligi(baslangic, bitis):
            try:
                sonuc = bilet_kontrol(tarih)
                if sonuc:
                    tren, gun, vagon = sonuc
                    mesaj = (
                        "🎉 BİLET BULUNDU!\n\n"
                        "📍 Ankara → Tatvan\n"
                        f"📅 Tarih: {gun}\n"
                        f"🚆 Tren: {tren}\n"
                        f"🛏️ Vagon: {vagon}\n"
                        "👥 Kişi: 4"
                    )
                    telegram_mesaj(mesaj)
                    with open(BULUNDU_DOSYA, "w") as f:
                        f.write("bulundu")
                    exit()

            except Exception:
                if not os.path.exists(HATA_DOSYA):
                    telegram_mesaj("⚠️ Bot hata aldı! TCDD sistemi değişmiş olabilir.")
                    with open(HATA_DOSYA, "w") as f:
                        f.write("hata")

        time.sleep(300)
