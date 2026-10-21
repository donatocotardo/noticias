import argparse
import time

import requests

from comandos import responder
from utils import API, CHAT_ID, enviar_mensajes


def _updates(offset: int | None = None, timeout: int = 0) -> list[dict]:
    params = {"timeout": timeout, "allowed_updates": '["message"]'}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"{API}/getUpdates", params=params, timeout=timeout + 15)
    r.raise_for_status()
    return r.json()["result"]


def _atender(update: dict) -> None:
    msg = update.get("message") or {}
    if str(msg.get("chat", {}).get("id")) != str(CHAT_ID):
        return  # ignora a cualquiera que no seas tú
    texto = (msg.get("text") or "").strip()
    if not texto.startswith("/"):
        return
    try:
        respuesta = responder(texto)
    except Exception as e:
        print(f"[error] {e}")
        respuesta = ["⚠️ No he podido procesar ese comando."]
    enviar_mensajes(respuesta)


def una_vez() -> int:
    """Atiende los mensajes pendientes y termina (para GitHub Actions)."""
    updates = _updates()
    for u in updates:
        _atender(u)
    if updates:
        # Confirma a Telegram que ya los has leído: los descarta del servidor
        _updates(offset=max(u["update_id"] for u in updates) + 1)
    return len(updates)


def bucle() -> None:
    """Escucha de forma continua (para probar en tu PC)."""
    offset = None
    print("Escuchando... (Ctrl+C para parar)")
    while True:
        try:
            for u in _updates(offset, timeout=30):
                offset = u["update_id"] + 1
                _atender(u)
        except requests.RequestException as e:
            print(f"[red] {e}")
            time.sleep(5)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--una-vez", action="store_true")
    g.add_argument("--bucle", action="store_true")
    a = p.parse_args()
    if a.una_vez:
        print(f"{una_vez()} mensajes atendidos")
    else:
        bucle()