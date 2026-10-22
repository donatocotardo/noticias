import json
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

from temas import limpiar_html

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
    "Accept-Language": "es-ES,es;q=0.9",
}

def cargar_feeds(ruta: str = "feeds.json") -> list[dict]:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _fecha(entrada) -> datetime | None:
    """feedparser entrega la fecha ya normalizada a UTC en *_parsed."""
    t = entrada.get("published_parsed") or entrada.get("updated_parsed")
    if not t:
        return None
    return datetime(*t[:6], tzinfo=timezone.utc)


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
                "titulo": limpiar_html(e.get("title", "")),
                "enlace": e.get("link", ""),
                "resumen": e.get("summary", "").strip(),
                "fecha": e.get("published", ""),
                "fecha_dt": _fecha(e),
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