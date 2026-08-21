import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

# Palabras clave jurídicas para filtrar disposiciones de máxima relevancia
PALABRAS_CLAVE_JURIDICAS = [
    'penal', 'penalista', 'juicios', 'ley criminal', 'constitución española',
    'derecho penal', 'jurisprudencia', 'derecho penitenciario', 'civil', 'procesal',
    'enjuiciamiento', 'laboral', 'trabajadores', 'tributario', 'mercantil',
    'contencioso', 'administrativo', 'tribunal supremo', 'audiencia', 'derecho'
]

# Códigos Consolidados de Referencia Oficial en España (BOE)
CODIGOS_CONSOLIDADOS_MAPA = {
    "CONSTITUCION": {
        "id": "BOE-A-1978-31229",
        "nombre": "Constitución Española (1978)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229",
        "materia": "Constitucional"
    },
    "CODIGO_PENAL": {
        "id": "BOE-A-1995-25444",
        "nombre": "Código Penal (Ley Orgánica 10/1995)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444",
        "materia": "Penal"
    },
    "CODIGO_CIVIL": {
        "id": "BOE-A-1889-4763",
        "nombre": "Código Civil (Real Decreto de 24 de julio de 1889)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763",
        "materia": "Civil"
    },
    "LECRIM": {
        "id": "BOE-A-1882-6036",
        "nombre": "Ley de Enjuiciamiento Criminal (Real Decreto de 14 de septiembre de 1882)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1882-6036",
        "materia": "Procesal Penal"
    },
    "LEC": {
        "id": "BOE-A-2000-323",
        "nombre": "Ley 1/2000, de 7 de enero, de Enjuiciamiento Civil",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2000-323",
        "materia": "Procesal Civil"
    },
    "ESTATUTO_TRABAJADORES": {
        "id": "BOE-A-2015-11430",
        "nombre": "Estatuto de los Trabajadores (Real Decreto Legislativo 2/2015)",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-11430",
        "materia": "Laboral"
    },
    "LPACAP": {
        "id": "BOE-A-2015-10565",
        "nombre": "Ley 39/2015, del Procedimiento Administrativo Común de las AAPP",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-10565",
        "materia": "Administrativo"
    }
}


def obtener_leyes_del_dia_xml(fecha: Optional[date] = None) -> List[Dict[str, Any]]:
    """Consulta el feed XML oficial del sumario del BOE para una fecha dada."""
    if fecha is None:
        fecha = date.today()

    url = f"https://www.boe.es/diario_boe/xml.php?id=BOE-S-{fecha.strftime('%Y%m%d')}"
    
    try:
        respuesta = requests.get(url, timeout=12)
        if b"<?xml" not in respuesta.content[:100]:
            return []
        
        raiz = ET.fromstring(respuesta.content)
        leyes = []
        for item in raiz.findall(".//item"):
            id_boe = item.findtext("id", "")
            titulo = item.findtext("titulo", "")
            url_pdf = item.findtext("url_pdf", "")
            url_eli = item.findtext("url_eli", "")
            if id_boe and titulo:
                url_web = f"https://www.boe.es/buscar/doc.php?id={id_boe}"
                url_pdf_full = f"https://www.boe.es{url_pdf}" if url_pdf else ""
                leyes.append({
                    "id": id_boe,
                    "titulo": titulo,
                    "url_pdf": url_pdf_full,
                    "url_web": url_web,
                    "url_eli": url_eli,
                    "fecha": fecha.strftime("%Y-%m-%d"),
                    "es_relevante": es_relevante_juridico(titulo)
                })
        return leyes
    except Exception as e:
        print(f"Error consultando BOE XML: {e}")
        return []


def es_relevante_juridico(titulo: str) -> bool:
    """Filtra disposiciones y leyes por interés procesal y legislativo."""
    titulo_lower = titulo.lower()
    return any(palabra in titulo_lower for palabra in PALABRAS_CLAVE_JURIDICAS)


def ultimo_dia_laboral() -> date:
    """Calcula el último día hábil (lunes a viernes)."""
    hoy = date.today()
    for i in range(7):
        dia = hoy - timedelta(days=i)
        if dia.weekday() < 5:
            return dia
    return hoy
