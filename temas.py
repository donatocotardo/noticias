import html
import json
import re
import unicodedata
from pathlib import Path

RUTA = Path("topics.json")


def cargar_temas() -> dict[str, list[str]]:
    if not RUTA.exists():
        return {}
    return json.loads(RUTA.read_text(encoding="utf-8"))


def guardar_temas(temas: dict[str, list[str]]) -> None:
    RUTA.write_text(json.dumps(temas, ensure_ascii=False, indent=2), encoding="utf-8")


def anadir_tema(nombre: str, palabras: list[str] | None = None) -> None:
    temas = cargar_temas()
    temas[nombre] = [normalizar(p) for p in (palabras or [nombre])]
    guardar_temas(temas)


def quitar_tema(nombre: str) -> bool:
    temas = cargar_temas()
    existente = next((t for t in temas if normalizar(t) == normalizar(nombre)), None)
    if existente is None:
        return False
    del temas[existente]
    guardar_temas(temas)
    return True


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar sin problemas."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def limpiar_html(texto: str) -> str:
    for _ in range(2):  # dos pasadas: algunos feeds escapan las etiquetas
        texto = html.unescape(re.sub(r"<[^>]+>", " ", texto))
    return re.sub(r"\s+", " ", texto).strip()


def _coincide(palabra: str, texto: str) -> bool:
    return re.search(rf"\b{re.escape(palabra)}\b", texto) is not None


def puntuar(noticia: dict, temas: dict[str, list[str]]) -> dict:
    """Devuelve los temas que casan y una puntuación (título pesa más que el resumen)."""
    titulo = normalizar(noticia["titulo"])
    resumen = normalizar(limpiar_html(noticia["resumen"]))
    casan, puntos = [], 0
    for tema, palabras in temas.items():
        p = 0
        for palabra in palabras:
            if _coincide(palabra, titulo):
                p += 3
            elif _coincide(palabra, resumen):
                p += 1
        if p:
            casan.append(tema)
            puntos += p
    return {"temas": casan, "puntuacion": puntos}


def filtrar(noticias: list[dict], temas: dict[str, list[str]]) -> list[dict]:
    relevantes = []
    for n in noticias:
        r = puntuar(n, temas)
        if r["puntuacion"] > 0:
            relevantes.append({**n, **r})
    return sorted(relevantes, key=lambda n: n["puntuacion"], reverse=True)


if __name__ == "__main__":
    from noticias import obtener_todas

    todas = obtener_todas()
    relevantes = filtrar(todas, cargar_temas())
    print(f"\n{len(relevantes)} relevantes de {len(todas)}\n")
    for n in relevantes[:15]:
        print(f"[{n['puntuacion']}] {', '.join(n['temas'])} | {n['titulo']}")
        print(f"    {n['fuente']} - {n['enlace']}")