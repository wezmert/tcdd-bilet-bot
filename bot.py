import os
import requests
import time

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def telegram_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mesaj
    }
    requests.post(url, data=data)

if name == "main":
    telegram_mesaj("✅ Bot çalıştı. Bu test mesajıdır.")
    while True:
        time.sleep(300)
