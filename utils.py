import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API = f"https://api.telegram.org/bot{TOKEN}"


def enviar_mensaje(texto: str) -> None:
    r = requests.post(
        f"{API}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": texto,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    r.raise_for_status()


def enviar_mensajes(mensajes: list[str]) -> None:
    for m in mensajes:
        enviar_mensaje(m)
        time.sleep(1)


if __name__ == "__main__":
    enviar_mensaje("Hola desde Python 👋")
    print("Enviado")