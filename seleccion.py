import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

VISTAS = Path(os.environ.get("DATOS_DIR", ".")) / "seen.json"


def solo_recientes(noticias: list[dict], horas: int = 36) -> list[dict]:
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    sin_fecha = sum(1 for n in noticias if not n.get("fecha_dt"))
    if sin_fecha:
        print(f"[aviso] {sin_fecha} noticias sin fecha descartadas")
    return [n for n in noticias if n.get("fecha_dt") and n["fecha_dt"] >= limite]


def _clave(n: dict) -> str:
    return n["enlace"].split("?")[0]


def cargar_vistas() -> dict[str, str]:
    if not VISTAS.exists():
        return {}
    try:
        return json.loads(VISTAS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def guardar_vistas(vistas: dict[str, str], dias: int = 30) -> None:
    """Guarda las vistas y descarta las de más de `dias`, para que el archivo no crezca."""
    limite = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    vigentes = {k: v for k, v in vistas.items() if v >= limite}
    VISTAS.write_text(json.dumps(vigentes, indent=2), encoding="utf-8")


def quitar_vistas(noticias: list[dict], vistas: dict[str, str]) -> list[dict]:
    return [n for n in noticias if _clave(n) not in vistas]


def marcar_vistas(noticias: list[dict], vistas: dict[str, str]) -> None:
    ahora = datetime.now(timezone.utc).isoformat()
    for n in noticias:
        vistas[_clave(n)] = ahora


def equilibrar(
    noticias: list[dict], max_total: int = 20, max_por_tema: int = 6
) -> list[dict]:
    """Recorre las noticias (ya ordenadas) y limita cuántas entran por tema."""
    cuenta: dict[str, int] = {}
    elegidas = []
    for n in noticias:
        if len(elegidas) >= max_total:
            break
        if any(cuenta.get(t, 0) < max_por_tema for t in n["temas"]):
            elegidas.append(n)
            for t in n["temas"]:
                cuenta[t] = cuenta.get(t, 0) + 1
    return elegidas