import math
import re
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .legal_chunker import LegalChunk, chunk_texto_legal
from .boe_scraper import CODIGOS_CONSOLIDADOS_MAPA
from .cendoj_client import JURISPRUDENCIA_REPOSITORIO_BASE, enlazar_jurisprudencia_automatica
from ..config import VECTOR_DIR

INDEX_FILE_PATH = VECTOR_DIR / "ammaia_legal_index.json"
OLD_INDEX_PATH = VECTOR_DIR / "ammayia_legal_index.json"

# IDs Oficiales del BOE para generar enlaces directos a cualquier artículo
BOE_IDS_MAPA = {
    "constitucion": "BOE-A-1978-31229",
    "codigo penal": "BOE-A-1995-25444",
    "penal": "BOE-A-1995-25444",
    "codigo civil": "BOE-A-1889-4763",
    "civil": "BOE-A-1889-4763",
    "enjuiciamiento criminal": "BOE-A-1882-6036",
    "lecrim": "BOE-A-1882-6036",
    "enjuiciamiento civil": "BOE-A-2000-323",
    "lec": "BOE-A-2000-323",
    "estatuto de los trabajadores": "BOE-A-2015-11430",
    "trabajadores": "BOE-A-2015-11430",
    "procedimiento administrativo": "BOE-A-2015-10565",
    "lpacap": "BOE-A-2015-10565",
    "regimen juridico": "BOE-A-2015-10566",
    "lrjsp": "BOE-A-2015-10566"
}

def generar_enlace_directo_boe(norma: str, articulo: str) -> str:
    """
    Genera un enlace DIRECTO Y EXACTO al artículo dentro del texto consolidado oficial del BOE.
    Ejemplo: Código Penal + Artículo 138 -> https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a138
    """
    norma_lower = norma.lower()
    boe_id = None
    for clave, bid in BOE_IDS_MAPA.items():
        if clave in norma_lower:
            boe_id = bid
            break

    # Extraer número del artículo (ej: 'Artículo 138' -> '138', 'Art. 20.4' -> '20')
    match_num = re.search(r'\b(?:art[íi]culo|art\.?)\s*(\d+)', articulo.lower())
    num_art = match_num.group(1) if match_num else ""

    if boe_id:
        if num_art:
            return f"https://www.boe.es/buscar/act.php?id={boe_id}#a{num_art}"
        return f"https://www.boe.es/buscar/act.php?id={boe_id}"
    
    return "https://www.boe.es/legislacion/codigos/"

def generar_enlace_cendoj(roj: str, ecli: str) -> str:
    """Genera enlace oficial de búsqueda directa a la sentencia en el portal de jurisprudencia del CENDOJ / CGPJ."""
    termino = ecli if ecli else roj
    termino_clean = termino.replace(" ", "+")
    return f"https://www.poderjudicial.es/search/doSearch?query={termino_clean}"


# ── Base de Conocimiento Jurídica Central con ENLACES EXACTOS AL ARTÍCULO ──
CONOCIMIENTO_LEGAL_INICIAL = [
    # CONSTITUCIÓN ESPAÑOLA (1978)
    {
        "norma": "Constitución Española (1978)",
        "articulo": "Artículo 14",
        "materia": "Constitucional",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229#a14",
        "contenido": "Los españoles son iguales ante la ley, sin que pueda prevalecer discriminación alguna por razón de nacimiento, raza, sexo, religión, opinión o cualquier otra condición o circunstancia personal o social."
    },
    {
        "norma": "Constitución Española (1978)",
        "articulo": "Artículo 24",
        "materia": "Constitucional / Procesal",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229#a24",
        "contenido": "1. Todas las personas tienen derecho a obtener la tutela efectiva de los jueces y tribunales en el ejercicio de sus derechos e intereses legítimos, sin que, en ningún caso, pueda producirse indefensión. 2. Asimismo, todos tienen derecho al Juez ordinario predeterminado por la ley, a la defensa y a la asistencia de letrado, a ser informados de la acusación formulada contra ellos, a un proceso público sin dilaciones indebidas y con todas las garantías, a utilizar los medios de prueba pertinentes para su defensa, a no declarar contra sí mismos, a no confesarse culpables y a la presunción de inocencia."
    },
    # CÓDIGO PENAL (Ley Orgánica 10/1995)
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 20",
        "materia": "Penal - Eximentes",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a20",
        "contenido": "Están exentos de responsabilidad criminal: 1.º El que al tiempo de cometer la infracción penal, a causa de cualquier anomalía o alteración psíquica, no pueda comprender la ilicitud del hecho o actuar conforme a esa comprensión. 4.º El que obre en defensa de la persona o derechos propios o ajenos (Legítima Defensa), siempre que concurran los requisitos: agresión ilegítima, necesidad racional del medio empleado para impedirla o repelerla, y falta de provocación suficiente por parte del defensor."
    },
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 138",
        "materia": "Penal - Homicidio",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a138",
        "contenido": "1. El que matare a otro será castigado, como reo de homicidio, con la pena de prisión de diez a quince años. 2. Los hechos serán castigados con la pena superior en grado en los siguientes casos: a) cuando concurra en su comisión alguna de las circunstancias del apartado 1 del artículo 140, o b) cuando los hechos sean además constitutivos de un delito de atentado del artículo 550."
    },
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 139",
        "materia": "Penal - Asesinato",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a139",
        "contenido": "1. Será castigado con la pena de prisión de quince a veinticinco años, como reo de asesinato, el que matare a otro concurriendo alguna de las circunstancias siguientes: 1.ª Con alevosía. 2.ª Por precio, recompensa o promesa. 3.ª Con ensañamiento, aumentando deliberada e inhumanamente el dolor del ofendido. 4.ª Para facilitar la comisión de otro delito o para evitar que se descubra."
    },
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 202",
        "materia": "Penal - Allanamiento de Morada",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a202",
        "contenido": "1. El particular que, sin habitar en ella, entrare en morada ajena o se mantuviere en la misma contra la voluntad de su morador, será castigado con la pena de prisión de seis meses a dos años. 2. Si el hecho se ejecutare con violencia o intimidación la pena será de prisión de uno a cuatro años y multa de seis a doce meses."
    },
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 234",
        "materia": "Penal - Hurto",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a234",
        "contenido": "1. El que, con ánimo de lucro, tomare las cosas muebles ajenas sin la voluntad de su dueño será castigado, como reo de hurto, con la pena de prisión de seis a dieciocho meses si la cuantía de lo sustraído excede de 400 euros. 2. Se impondrá una pena de multa de uno a tres meses si la cuantía del objeto sustraído no excediese de 400 euros, salvo si concurriese alguna de las circunstancias del artículo 235."
    },
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 238",
        "materia": "Penal - Robo con Fuerza",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a238",
        "contenido": "Son reos del delito de robo con fuerza en las cosas los que ejecuten el hecho cuando concurra alguna de las circunstancias siguientes: 1.ª Escalamiento. 2.ª Rompimiento de pared, techo o suelo, o fractura de puerta o ventana. 3.ª Fractura de armarios, arcas u otra clase de muebles u objetos cerrados o sellados, o forzamiento de sus cerraduras o descubrimiento de sus claves. 4.ª Uso de llaves falsas. 5.ª Inutilización de sistemas específicos de alarma o guarda."
    },
    {
        "norma": "Código Penal (LO 10/1995)",
        "articulo": "Artículo 248",
        "materia": "Penal - Estafa",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a248",
        "contenido": "1. Cometen estafa los que, con ánimo de lucro, utilizaren engaño bastante para producir error en otro, induciéndolo a realizar un acto de disposición en perjuicio propio o ajeno. 2. También se consideran reos de estafa los que, con ánimo de lucro y valiéndose de alguna manipulación informática o artificio semejante, consigan una transferencia no consentida de cualquier activo patrimonial."
    },
    # CÓDIGO CIVIL (1889)
    {
        "norma": "Código Civil",
        "articulo": "Artículo 1902",
        "materia": "Civil - Responsabilidad Extracontractual",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763#a1902",
        "contenido": "El que por acción u omisión causa daño a otro, interviniendo culpa o negligencia, está obligado a reparar el daño causado."
    },
    {
        "norma": "Código Civil",
        "articulo": "Artículo 1255",
        "materia": "Civil - Contratos / Autonomía de la Voluntad",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763#a1255",
        "contenido": "Los contratantes pueden establecer los pactos, cláusulas y condiciones que tengan por conveniente, siempre que no sean contrarios a las leyes, a la moral ni al orden público."
    },
    # LEY DE ENJUICIAMIENTO CIVIL (Ley 1/2000)
    {
        "norma": "Ley de Enjuiciamiento Civil (Ley 1/2000)",
        "articulo": "Artículo 448",
        "materia": "Procesal Civil - Recursos",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2000-323#a448",
        "contenido": "1. Contra las resoluciones de los Tribunales y Letrados de la Administración de Justicia que les afecten desfavorablemente, las partes podrán interponer los recursos previstos en la ley. 2. Los plazos para recurrir se contarán desde el día siguiente a la notificación de la resolución."
    },
    # ESTATUTO DE LOS TRABAJADORES (RD Leg. 2/2015)
    {
        "norma": "Estatuto de los Trabajadores (RDL 2/2015)",
        "articulo": "Artículo 54",
        "materia": "Laboral - Despido Disciplinario",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-11430#a54",
        "contenido": "1. El contrato de trabajo podrá extinguirse por decisión del empresario, mediante despido basado en un incumplimiento grave y culpable del trabajador. 2. Se considerarán incumplimientos contractuales: a) Las faltas repetidas e injustificadas de asistencia o puntualidad al trabajo. b) La indisciplina o desobediencia en el trabajo. c) Las ofensas verbales o físicas al empresario o a las personas que trabajan en la empresa. d) La transgresión de la buena fe contractual, así como el abuso de confianza."
    },
    {
        "norma": "Estatuto de los Trabajadores (RDL 2/2015)",
        "articulo": "Artículo 56",
        "materia": "Laboral - Despido Improcedente",
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-11430#a56",
        "contenido": "1. Cuando el despido sea declarado improcedente, el empresario, en el plazo de cinco días desde la notificación de la sentencia, podrá optar entre la readmisión del trabajador o el abono de una indemnización equivalente a treinta y tres días de salario por año de servicio, prorrateándose por meses los períodos de tiempo inferiores a un año, hasta un máximo de veinticuatro mensualidades."
    }
]


class LegalVectorStore:
    """Motor de Búsqueda Híbrida Legal con enlaces directos y persistencia."""
    def __init__(self):
        self.documentos: List[Dict[str, Any]] = []
        self._cargar_indice_o_base()

    def _cargar_indice_o_base(self):
        # Cargar base por defecto con enlaces exactos a cada artículo
        for item in CONOCIMIENTO_LEGAL_INICIAL:
            url_directa = generar_enlace_directo_boe(item["norma"], item["articulo"])
            self.agregar_documento(
                norma=item["norma"],
                articulo=item["articulo"],
                contenido=item["contenido"],
                url_boe=url_directa,
                materia=item["materia"],
                guardar_disco=False
            )
        
        # Cargar jurisprudencia base multijurisdiccional (TS, TC, TEDH HUDOC y TJUE CURIA)
        for j in JURISPRUDENCIA_REPOSITORIO_BASE:
            url_juris = j.get("url") or enlazar_jurisprudencia_automatica(j["roj"])
            self.agregar_documento(
                norma=f"{j['tribunal']} ({j['sala']}) - {j['roj']}",
                articulo=f"Sentencia {j['fecha']} (Rec. {j['recurso']})",
                contenido=f"Resumen: {j['resumen']}\nFundamentos Jurídicos: {j['fundamentos']}",
                url_boe=url_juris,
                materia=j["materia"],
                es_jurisprudencia=True,
                guardar_disco=False
            )
        
        # Cargar documentos adicionales si existen en disco
        if os.path.exists(INDEX_FILE_PATH):
            try:
                with open(INDEX_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        url_final = item.get("url_boe") or generar_enlace_directo_boe(item["norma"], item.get("articulo", ""))
                        self.agregar_documento(
                            norma=item["norma"],
                            articulo=item.get("articulo", ""),
                            contenido=item["contenido"],
                            url_boe=url_final,
                            materia=item.get("materia", "General"),
                            es_jurisprudencia=item.get("es_jurisprudencia", False),
                            guardar_disco=False
                        )
            except Exception as e:
                print(f"[Vector Store Error] {e}")

        self.guardar_en_disco()

    def guardar_en_disco(self):
        try:
            VECTOR_DIR.mkdir(parents=True, exist_ok=True)
            export_data = []
            for doc in self.documentos:
                export_data.append({
                    "norma": doc["norma"],
                    "articulo": doc["articulo"],
                    "contenido": doc["contenido"],
                    "url_boe": doc["url_boe"],
                    "materia": doc["materia"],
                    "es_jurisprudencia": doc.get("es_jurisprudencia", False)
                })
            with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Vector Store] Error guardando: {e}")

    def agregar_documento(self, norma: str, articulo: str, contenido: str, url_boe: str, materia: str = "General", es_jurisprudencia: bool = False, guardar_disco: bool = True):
        # Auto-generar enlace directo si no viene con anchor
        if not url_boe or url_boe == "https://www.boe.es":
            if not es_jurisprudencia:
                url_boe = generar_enlace_directo_boe(norma, articulo)

        doc_id = f"{norma}_{articulo}".replace(" ", "_")
        for d in self.documentos:
            if d["id"] == doc_id:
                d["contenido"] = contenido
                d["url_boe"] = url_boe
                d["materia"] = materia
                return

        tokens = self._tokenizar(f"{norma} {articulo} {contenido}")
        self.documentos.append({
            "id": doc_id,
            "norma": norma,
            "articulo": articulo,
            "contenido": contenido,
            "url_boe": url_boe,
            "materia": materia,
            "es_jurisprudencia": es_jurisprudencia,
            "tokens": set(tokens),
            "texto_completo": f"{norma} {articulo} {contenido}".lower()
        })

        if guardar_disco:
            self.guardar_en_disco()

    def _tokenizar(self, texto: str) -> List[str]:
        texto_limpio = re.sub(r'[^\w\s]', ' ', texto.lower())
        return [w for w in texto_limpio.split() if len(w) > 2]

    def busqueda_hibrida(self, consulta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documentos:
            return []

        tokens_consulta = set(self._tokenizar(consulta))
        consulta_lower = consulta.lower()
        
        match_art = re.search(r'\b(?:art[íi]culo|art\.?)\s*(\d+)', consulta_lower)
        art_buscado = match_art.group(1) if match_art else ""

        puntuaciones = []

        for doc in self.documentos:
            score = 0.0
            texto_doc = doc["texto_completo"]
            tokens_doc = doc["tokens"]

            # 1. Coincidencia exacta de número de artículo (+12.0 boost)
            if art_buscado and (f"artículo {art_buscado}" in texto_doc or f"art. {art_buscado}" in texto_doc or doc["articulo"].endswith(art_buscado)):
                score += 12.0

            # 2. Coincidencia de tokens jurídicos
            interseccion = tokens_consulta.intersection(tokens_doc)
            if interseccion:
                score += len(interseccion) * 1.5

            # 3. Coincidencia de frase
            for t_palabra in tokens_consulta:
                if t_palabra in texto_doc:
                    score += 0.5

            if score > 0:
                puntuaciones.append((score, doc))

        puntuaciones.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in puntuaciones[:top_k]]


# Instancia global del vector store legal
vector_store = LegalVectorStore()
