import json
from pathlib import Path

import feedparser
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (agente-noticias)"}


def cargar_feeds(ruta: str = "feeds.json") -> list[dict]:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def leer_feed(feed: dict) -> list[dict]:
    """Descarga un feed y devuelve sus noticias como lista de diccionarios."""
    try:
        r = requests.get(feed["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[error] {feed['nombre']}: {e}")
        return []

    parsed = feedparser.parse(r.content)
    noticias = []
    for e in parsed.entries:
        noticias.append(
            {
                "fuente": feed["nombre"],
                "categoria": feed.get("categoria", ""),
                "titulo": e.get("title", "").strip(),
                "enlace": e.get("link", ""),
                "resumen": e.get("summary", "").strip(),
                "fecha": e.get("published", ""),
            }
        )
    return noticias


def obtener_todas() -> list[dict]:
    todas = []
    for feed in cargar_feeds():
        noticias = leer_feed(feed)
        print(f"{feed['nombre']}: {len(noticias)} noticias")
        todas.extend(noticias)
    return todas


if __name__ == "__main__":
    for n in obtener_todas()[:10]:
        print(f"- [{n['fuente']}] {n['titulo']}\n  {n['enlace']}")