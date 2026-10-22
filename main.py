import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from mensaje import formatear
from noticias import obtener_todas
from resumidor import resumir
from seleccion import (
    cargar_vistas,
    equilibrar,
    guardar_vistas,
    marcar_vistas,
    quitar_vistas,
    solo_recientes,
)
from temas import cargar_temas, filtrar
from utils import enviar_mensajes

load_dotenv()

MAX_ENVIO = 12
MARCA = Path(os.environ.get("DATOS_DIR", ".")) / "ultimo_envio.txt"


def _hoy() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _enviado_hoy() -> bool:
    return MARCA.exists() and MARCA.read_text().strip() == _hoy()


def main(enviar: bool, una_al_dia: bool = False, semantico: bool = False) -> None:
    if enviar and una_al_dia and _enviado_hoy():
        print("Ya se envió el resumen de hoy: nada que hacer")
        return

    temas = cargar_temas()
    todas = obtener_todas()

    recientes = solo_recientes(todas)
    print(f"\n{len(recientes)} recientes de {len(todas)}")

    vistas = cargar_vistas()
    nuevas = quitar_vistas(recientes, vistas)
    print(f"{len(nuevas)} nuevas (no vistas antes)")

    if semantico:
        from semantico import filtrar_hibrido

        filtradas = filtrar_hibrido(nuevas, temas)
    else:
        filtradas = filtrar(nuevas, temas)

    con_tema = sorted(
        filtradas,
        key=lambda n: (n["puntuacion"], n["fecha_dt"]),
        reverse=True,
    )
    candidatas = equilibrar(con_tema)
    print(f"{len(con_tema)} con tema, {len(candidatas)} candidatas para el LLM\n")
    if not candidatas:
        if enviar and todas:  # si no se descargó nada, no damos el día por hecho
            MARCA.write_text(_hoy())
        return

    elegidas = resumir(candidatas, temas)[:MAX_ENVIO]
    for n in elegidas:
        extra = f" (también en {', '.join(n['tambien_en'])})" if n["tambien_en"] else ""
        print(f"[{n['relevancia']}/10] {n['titulo']}")
        print(f"    {n['resumen_llm']}")
        print(f"    {n['fuente']}{extra} - {n['enlace']}\n")

    if not enviar:
        print("(prueba: no se ha enviado ni guardado nada)")
        return

    if elegidas:
        enviar_mensajes(formatear(elegidas))
        print("Enviado por Telegram")
    marcar_vistas(candidatas, vistas)
    guardar_vistas(vistas)
    print("seen.json actualizado")
    MARCA.write_text(_hoy())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--enviar",
        action="store_true",
        help="enviar por Telegram y guardar las noticias evaluadas en seen.json",
    )
    parser.add_argument(
        "--una-al-dia",
        action="store_true",
        help="no hacer nada si hoy ya se envió el resumen",
    )
    parser.add_argument(
        "--semantico",
        action="store_true",
        help="usar embeddings además de las palabras clave",
    )
    args = parser.parse_args()
    main(args.enviar, args.una_al_dia, args.semantico)