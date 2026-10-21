import re

from mensaje import trocear
from noticias import cargar_feeds, obtener_todas
from seleccion import solo_recientes
from temas import (
    anadir_tema,
    cargar_temas,
    filtrar,
    limpiar_html,
    normalizar,
    quitar_tema,
)

HORAS = 72
MAX_RESULTADOS = 8


def _categorias() -> list[str]:
    return sorted({f["categoria"] for f in cargar_feeds() if f.get("categoria")})


def _ayuda() -> str:
    cats = ", ".join("/" + c for c in _categorias())
    return (
        "Comandos:\n"
        "/temas — ver tus temas\n"
        "/anadir tema: palabra1, palabra2 — añade palabras al tema (lo crea si no existe)\n"
        "/quitar tema — borra el tema entero\n"
        "/quitar tema: palabra — quita solo esa palabra\n"
        "/buscar texto — buscar en todas las noticias recientes\n"
        f"Por categoría ({cats}): por ejemplo /futbol madrid\n"
        "Sin texto, te enseño lo último de esa categoría."
    )


def _buscar(consulta: str, categoria: str | None) -> list[str]:
    noticias = solo_recientes(obtener_todas(), horas=HORAS)
    if categoria:
        noticias = [n for n in noticias if normalizar(n["categoria"]) == categoria]
    if consulta:
        noticias = filtrar(noticias, {consulta: [normalizar(consulta)]})
    noticias.sort(key=lambda n: n["fecha_dt"], reverse=True)

    vistas, unicas = set(), []
    for n in noticias:
        clave = n["enlace"].split("?")[0]
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(n)
    unicas = unicas[:MAX_RESULTADOS]

    donde = f" en {categoria}" if categoria else ""
    que = f" «{consulta}»" if consulta else ""
    if not unicas:
        return [f"Nada reciente{que}{donde} (últimas {HORAS} h)."]

    bloques = [
        f"🔹 {n['titulo']}\n{limpiar_html(n['resumen'])[:200]}\n"
        f"{n['fuente']} · {n['fecha_dt']:%d/%m}\n{n['enlace']}"
        for n in unicas
    ]
    return trocear(bloques, f"🔎{que}{donde} — últimas {HORAS} h")


def _parsear(arg: str) -> tuple[str, list[str]]:
    """'tema: a, b' -> ('tema', ['a', 'b']);  'tema' -> ('tema', [])"""
    nombre, sep, resto = arg.partition(":")
    palabras = [p.strip() for p in resto.split(",") if p.strip()] if sep else []
    return nombre.strip(), palabras


def _anadir(arg: str) -> list[str]:
    nombre, palabras = _parsear(arg)
    if not nombre:
        return ["Uso: /anadir tema   o   /anadir tema: palabra1, palabra2"]
    clave, nuevas, todas = anadir_tema(nombre, palabras or None)
    if not nuevas:
        return [f"«{clave}» ya tenía eso. Palabras: {', '.join(todas)}"]
    return [f"✅ «{clave}»: añadido {', '.join(nuevas)}\nAhora: {', '.join(todas)}"]


def _quitar(arg: str) -> list[str]:
    nombre, palabras = _parsear(arg)
    if not nombre:
        return ["Uso: /quitar tema   o   /quitar tema: palabra"]
    if quitar_tema(nombre, palabras or None):
        if palabras:
            return [f"🗑️ Quitado de «{nombre}»: {', '.join(palabras)}"]
        return [f"🗑️ Tema «{nombre}» quitado."]
    return ["No encuentro eso en tus temas. Mira /temas."]


def _temas() -> list[str]:
    temas = cargar_temas()
    if not temas:
        return ["No tienes temas. Añade uno con /anadir."]
    return ["Tus temas:\n" + "\n".join(f"• {t}: {', '.join(p)}" for t, p in temas.items())]


def responder(texto: str) -> list[str]:
    """Recibe el texto de un comando y devuelve los mensajes a enviar."""
    partes = re.split(r"\s+", texto.strip(), maxsplit=1)
    cmd = normalizar(partes[0].lstrip("/").split("@")[0])
    arg = partes[1].strip() if len(partes) > 1 else ""

    if cmd in ("start", "ayuda", "help"):
        return [_ayuda()]
    if cmd == "temas":
        return _temas()
    if cmd in ("anadir", "add"):
        return _anadir(arg)
    if cmd in ("quitar", "borrar"):
        return _quitar(arg)
    if cmd == "buscar":
        return _buscar(arg, None)
    if cmd in {normalizar(c) for c in _categorias()}:
        return _buscar(arg, cmd)
    return ["No conozco ese comando. Escribe /ayuda."]