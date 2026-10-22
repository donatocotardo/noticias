import argparse
import os

import numpy as np
from dotenv import load_dotenv

from temas import cargar_temas, limpiar_html, puntuar

load_dotenv()

MODELO = os.environ.get("EMBED_MODEL") or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
UMBRAL = float(os.environ.get("EMBED_UMBRAL") or "0.55")

_modelo = None


def _cargar_modelo():
    global _modelo
    if _modelo is None:
        from fastembed import TextEmbedding

        _modelo = TextEmbedding(MODELO)
    return _modelo


def _prefijos() -> tuple[str, str]:
    """Los modelos E5 necesitan prefijos distintos para consultas y textos; los demás no."""
    if "e5" in MODELO.lower():
        return "query: ", "passage: "
    return "", ""


def _vectorizar(textos: list[str], prefijo: str) -> np.ndarray:
    v = np.array(
        list(_cargar_modelo().embed([prefijo + t for t in textos])), dtype=float
    )
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def similitudes(noticias: list[dict], temas: dict[str, list[str]]) -> list[dict[str, float]]:
    """Para cada noticia, su similitud máxima con cada tema."""
    if not noticias or not temas:
        return [{} for _ in noticias]

    pq, pp = _prefijos()
    frases, columnas = [], {}
    for tema, palabras in temas.items():
        columnas[tema] = []
        for frase in (tema, f"{tema}: {', '.join(palabras)}"):
            columnas[tema].append(len(frases))
            frases.append(frase)

    emb_temas = _vectorizar(frases, pq)
    textos = [f"{n['titulo']}. {limpiar_html(n['resumen'])[:300]}" for n in noticias]
    emb_noticias = _vectorizar(textos, pp)

    sims = emb_noticias @ emb_temas.T
    return [
        {tema: float(max(sims[i, c] for c in cols)) for tema, cols in columnas.items()}
        for i in range(len(noticias))
    ]


def filtrar_hibrido(
    noticias: list[dict], temas: dict[str, list[str]], umbral: float = UMBRAL
) -> list[dict]:
    """Pasa lo que case por palabras clave o por similitud con algún tema."""
    if not noticias or not temas:
        return []

    resultado = []
    for n, sims in zip(noticias, similitudes(noticias, temas)):
        kw = puntuar(n, temas)
        sem = [t for t, s in sims.items() if s >= umbral]
        if not kw["temas"] and not sem:
            continue
        mejor = max(sims.values())
        extra = round(mejor * 10) if sem else 0
        resultado.append(
            {
                **n,
                "temas": list(dict.fromkeys(kw["temas"] + sem)),
                "puntuacion": kw["puntuacion"] + extra,
                "similitud": mejor,
            }
        )
    return sorted(resultado, key=lambda n: n["puntuacion"], reverse=True)


if __name__ == "__main__":
    from noticias import obtener_todas
    from seleccion import solo_recientes

    p = argparse.ArgumentParser()
    p.add_argument("--umbral", type=float, default=UMBRAL)
    args = p.parse_args()

    temas = cargar_temas()
    if not temas:
        raise SystemExit("No hay temas en topics.json")

    noticias = solo_recientes(obtener_todas())
    filas = []
    for n, sims in zip(noticias, similitudes(noticias, temas)):
        tema, s = max(sims.items(), key=lambda kv: kv[1])
        filas.append((s, tema, bool(puntuar(n, temas)["temas"]), n))
    filas.sort(key=lambda f: f[0], reverse=True)

    solo_emb = [f for f in filas if f[0] >= args.umbral and not f[2]]
    con_kw = sum(1 for f in filas if f[2])
    print(f"\nUmbral {args.umbral}: {con_kw} por palabras clave, {len(solo_emb)} solo por embeddings\n")

    print(" Solo por embeddings")
    for s, tema, _, n in solo_emb[:30]:
        print(f"[{s:.2f}] {tema} | {n['titulo']}  ({n['fuente']})")

    justo_debajo = [f for f in filas if args.umbral - 0.08 <= f[0] < args.umbral and not f[2]]
    print("\nJusto por debajo del umbral, por si se escapa algo interesante")
    for s, tema, _, n in justo_debajo[:15]:
        print(f"[{s:.2f}] {tema} | {n['titulo']}  ({n['fuente']})")