import os
import time
import json
import requests
from datetime import datetime, timedelta

# Telegram bilgileri (GitHub Secrets)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))

# Dosyalar
BULUNDU_DOSYA = "bulundu.txt"
HATA_DOSYA = "hata.txt"
DURUM_DOSYA = "durum.json"
UPDATE_DOSYA = "update_id.txt"


def telegram_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj}
    requests.post(url, data=data, timeout=10)


def durum_yukle():
    if os.path.exists(DURUM_DOSYA):
        with open(DURUM_DOSYA, "r") as f:
            return json.load(f)
    return {}


def durum_kaydet(durum):
    with open(DURUM_DOSYA, "w") as f:
        json.dump(durum, f)


def son_update_id_yukle():
    if os.path.exists(UPDATE_DOSYA):
        return int(open(UPDATE_DOSYA).read().strip())
    return 0


def son_update_id_kaydet(uid):
    with open(UPDATE_DOSYA, "w") as f:
        f.write(str(uid))


def telegram_komut_kontrol():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": son_update_id_yukle() + 1}
    r = requests.get(url, params=params, timeout=10).json()

    for upd in r.get("result", []):
        uid = upd["update_id"]
        son_update_id_kaydet(uid)

        msg = upd.get("message", {})
        if not msg:
            continue

        chat_id = msg["chat"]["id"]
        if chat_id != CHAT_ID:
            continue

        text = msg.get("text", "").lower()

        if "çalışıyor" in text or "calisiyor" in text:
            telegram_mesaj("🤖 Evet, buradayım. Bot çalışıyor ve bilet arıyorum.")


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

    # Bilet bulunduysa tamamen dur
    if os.path.exists(BULUNDU_DOSYA):
        exit()

    durum = durum_yukle()
    bugun = datetime.now().strftime("%Y-%m-%d")

    # İlk başlama mesajı
    if not durum.get("basladi"):
        telegram_mesaj("🤖 TCDD bilet botu aktif. Kontroller başladı.")
        durum["basladi"] = True

    # Günlük sağlık mesajı
    if durum.get("son_gunluk_mesaj") != bugun:
        telegram_mesaj("✅ Bot çalışıyor, hâlâ bilet arıyorum.")
        durum["son_gunluk_mesaj"] = bugun

    durum_kaydet(durum)

    baslangic = datetime(2026, 1, 22)
    bitis = datetime(2026, 2, 3)

    while True:
        # Telegram'dan "çalışıyor musun" kontrolü
        telegram_komut_kontrol()

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
                    open(BULUNDU_DOSYA, "w").write("ok")
                    exit()

except Exception:
                if not os.path.exists(HATA_DOSYA):
                    telegram_mesaj("⚠️ Bot hata aldı! TCDD sistemi değişmiş olabilir.")
                    open(HATA_DOSYA, "w").write("hata")

        time.sleep(300)
