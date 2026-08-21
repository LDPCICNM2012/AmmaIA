from fastapi import APIRouter
from datetime import date
from typing import Optional, List, Dict, Any

from ..rag.boe_scraper import (
    obtener_leyes_del_dia_xml,
    ultimo_dia_laboral,
    CODIGOS_CONSOLIDADOS_MAPA
)

router = APIRouter(prefix="/boe", tags=["Boletín Oficial del Estado (BOE)"])

@router.get("/hoy")
def endpoint_boe_hoy(fecha_str: Optional[str] = None):
    """Devuelve las leyes y disposiciones publicadas en el BOE para hoy o el último día hábil."""
    if fecha_str:
        try:
            fecha = date.fromisoformat(fecha_str)
        except ValueError:
            fecha = ultimo_dia_laboral()
    else:
        fecha = ultimo_dia_laboral()

    leyes = obtener_leyes_del_dia_xml(fecha)
    leyes_relevantes = [l for l in leyes if l.get("es_relevante")]

    return {
        "fecha": fecha.strftime("%Y-%m-%d"),
        "total_publicadas": len(leyes),
        "total_relevantes": len(leyes_relevantes),
        "leyes": leyes_relevantes if leyes_relevantes else leyes[:15]
    }

@router.get("/codigos")
def endpoint_codigos_consolidados():
    """Devuelve el catálogo de Códigos Consolidados de España disponibles en AmmaIA."""
    return {"codigos": list(CODIGOS_CONSOLIDADOS_MAPA.values())}
