import argparse

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


def main(marcar: bool) -> None:
    temas = cargar_temas()
    todas = obtener_todas()

    recientes = solo_recientes(todas)
    print(f"\n{len(recientes)} recientes de {len(todas)}")

    vistas = cargar_vistas()
    nuevas = quitar_vistas(recientes, vistas)
    print(f"{len(nuevas)} nuevas (no vistas antes)")

    con_tema = sorted(
        filtrar(nuevas, temas),
        key=lambda n: (n["puntuacion"], n["fecha_dt"]),
        reverse=True,
    )
    candidatas = equilibrar(con_tema)
    print(f"{len(con_tema)} con tema, {len(candidatas)} candidatas para el LLM\n")
    if not candidatas:
        return

    elegidas = resumir(candidatas, temas)

    for n in elegidas:
        print(f"[{n['relevancia']}/10] {n['titulo']}")
        print(f"    {n['resumen_llm']}")
        print(f"    {n['fuente']} - {n['enlace']}\n")

    if marcar:
        marcar_vistas(candidatas, vistas)
        guardar_vistas(vistas)
        print("seen.json actualizado")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--marcar",
        action="store_true",
        help="guardar las noticias evaluadas en seen.json",
    )
    main(parser.parse_args().marcar)