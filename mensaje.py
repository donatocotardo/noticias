from datetime import datetime

LIMITE = 3900


def _bloque(n: dict) -> str:
    extra = f" (también en {', '.join(n['tambien_en'])})" if n.get("tambien_en") else ""
    return f"🔹 {n['titulo']}\n{n['resumen_llm']}\n{n['fuente']}{extra}\n{n['enlace']}"


def formatear(elegidas: list[dict]) -> list[str]:
    actual = f"📰 Tus noticias — {datetime.now():%d/%m/%Y}"
    mensajes = []
    for n in elegidas:
        bloque = _bloque(n)
        if len(actual) + len(bloque) + 2 > LIMITE:
            mensajes.append(actual)
            actual = bloque
        else:
            actual += "\n\n" + bloque
    mensajes.append(actual)
    return mensajes