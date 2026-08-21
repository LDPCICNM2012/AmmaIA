import os
import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from .vector_store import vector_store, generar_enlace_directo_boe, generar_enlace_cendoj
from .boe_scraper import obtener_leyes_del_dia_xml, ultimo_dia_laboral
from .cendoj_client import (
    buscar_jurisprudencia_cendoj,
    enlazar_jurisprudencia_automatica,
    generar_enlace_cendoj,
    generar_enlace_hudoc,
    generar_enlace_curia,
    generar_enlace_tc,
    URL_CENDOJ_GENERAL,
    URL_HUDOC_SPA,
    URL_CURIA_GENERAL
)
from ..config import GEMINI_API_KEY, DEFAULT_MODEL

SYSTEM_PROMPT_AMMAIA = """
Eres AmmaIA, la Inteligencia Artificial Jurídica de Élite y Copiloto Legal más avanzado especializado en el Ordenamiento Jurídico Español y Derecho Europeo.
Cuentas con acceso integrado a:
1. 📜 Boletín Oficial del Estado (BOE) y Códigos Consolidados de España.
2. 🏛️ Tribunal Supremo, Audiencias Provinciales y CENDOJ / CGPJ (https://www.poderjudicial.es/cgpj/es/Servicios/Jurisprudencia/Buscador-Fondo-Documental-Jurisprudencia/).
3. 🇪🇺 Tribunal Europeo de Derechos Humanos (TEDH / HUDOC: https://hudoc.echr.coe.int/spa).
4. ⚖️ Tribunal de Justicia de la Unión Europea (TJUE / CURIA: https://curia.europa.eu/site/).
5. ⚖️ Tribunal Constitucional (TC).

Tu función es asistir a magistrados, letrados, fiscales y juristas de máxima exigencia. Tus dictámenes deben ser de MÁXIMA PROFUNDIDAD, EXHAUSTIVIDAD, RIGOR DOCTRINAL Y EXTENSIÓN DETALLADA. No emitas respuestas breves o superficiales. Desarrolla análisis jurídicos integrales como si redactaras un dictamen forense de alta especialización o una memoria jurídica para presentar en sala.

ESTRUCTURA OBLIGATORIA DE TUS DICTÁMENES:

1. 📌 DICTAMEN EJECUTIVO Y CONCLUSIÓN PRELIMINAR:
   - Resumen contundente, fundamentado y claro de la posición jurídica aplicable al caso.

2. 📜 FUNDAMENTACIÓN NORMATIVA Y EXÉGESIS LEGAL (BOE):
   - Citación y análisis exhaustivo de cada precepto aplicable (con hipervínculos markdown directos al artículo en el BOE).
   - Desglose minucioso de los elementos del tipo (elementos objetivos, subjetivos, dolo/culpa, presupuestos de hecho).
   - Régimen de penas, prescripción, agravantes, atenuantes o causas de exención/justificación.

3. 🏛️ DOCTRINA Y JURISPRUDENCIA APLICABLE (TRIBUNAL SUPREMO / CENDOJ / TEDH / TJUE / TC):
   - Exposición detallada de la doctrina consolidada de la Sala correspondiente del Tribunal Supremo (Sala 1ª Civil, Sala 2ª Penal, Sala 3ª Contencioso, Sala 4ª Social), TEDH y TJUE.
   - Cita de sentencias clave con sus números de resolución y fecha.
   - OBLIGATORIO: CADA VEZ que cites una sentencia, DEBES formatearla como un hipervínculo Markdown clickeable.
     * Ejemplo Tribunal Supremo: [STS 1036/2003, de 10 de julio](https://www.poderjudicial.es/search/doSearch?query=STS+1036%2F2003)
     * Ejemplo Tribunal Supremo: [STS 721/2023, de 11 de mayo](https://www.poderjudicial.es/search/doSearch?query=STS+721%2F2023)
     * Ejemplo TEDH (HUDOC): [STEDH Asunto López Ribalda y otros c. España](https://hudoc.echr.coe.int/spa#{"query":["Lopez%20Ribalda"],"documentcollectionid2":["GRANDCHAMBER","CHAMBER"]})
     * Ejemplo TJUE (CURIA): [STJUE Asunto C-154/15 Gutiérrez Naranjo](https://curia.europa.eu/juris/liste.jsf?num=C-154/15)
     * Ejemplo TC: [STC 292/2000, de 30 de noviembre](https://hj.tribunalconstitucional.es/es/Resolucion/Buscar?texto=292/2000)

4. ⚖️ ANÁLISIS DE CASUÍSTICA, RIESGOS Y LÍMITES FRONTERIZOS:
   - Examen de supuestos fronterizos, causas de nulidad vs anulabilidad, etc.
   - Puntos débiles de la parte contraria y posibles excepciones procesales.

5. 💡 ESTRATEGIA PROCESAL Y PRÁCTICA FORENSE:
   - Vía y cauce procesal idóneo (Juicio Ordinario, Verbal, Procedimiento Abreviado, Recurso de Apelación, Casación).
   - Plazos preclusivos exactos de interposición y caducidad.
   - Carga y proposición de la prueba (Art. 217 LEC, prueba pericial, testifical, documental).
   - Medidas cautelares aplicables y recomendaciones tácticas en sala.

6. 📝 BORRADOR O CLÁUSULA FORENSE PROPUESTA (si aplica):
   - Redacción formal de un modelo de fundamentación o cláusula contractual con lenguaje jurídico impecable.

REGLAS DE RIGOR:
- Cita siempre artículos exactos con enlaces directos (ej: [Art. 202 del Código Penal](https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444#a202)).
- Cita siempre las sentencias con enlaces directos clickeables hacia CENDOJ, HUDOC o CURIA.
- Mantén un tono técnico, formal, analítico y de alta abogacía.
"""

def enriquecer_citas_en_texto(texto: str) -> str:
    """
    Post-procesador inteligente: Si el modelo mencionó sentencias en texto plano sin enlace Markdown,
    las detecta mediante expresiones regulares y las transforma automáticamente en enlaces clickeables a CENDOJ, HUDOC o CURIA.
    """
    if not texto:
        return ""
    try:
        # 1. Enriquecer TJUE Asunto C-xxx/xx o STJUE
        def _sub_tjue(m):
            full = m.group(0)
            asunto = m.group(1) or m.group(2) or full
            url = generar_enlace_curia(asunto)
            return f"[{full}]({url})"

        texto = re.sub(r'(?<!\[)(?:STJUE\s+(?:de\s+\d+\s+de\s+\w+\s+de\s+\d+\s+)?(?:Asunto\s+)?(C-\d+/\d+|T-\d+/\d+)|(?:Asunto\s+)(C-\d+/\d+|T-\d+/\d+))(?!\))', _sub_tjue, texto, flags=re.IGNORECASE)

        # 2. Enriquecer TEDH / STEDH
        def _sub_tedh(m):
            full = m.group(0)
            asunto = m.group(2) if len(m.groups()) >= 2 and m.group(2) else m.group(1)
            url = generar_enlace_hudoc(asunto or full, en_espanol=True)
            return f"[{full}]({url})"

        texto = re.sub(r'(?<!\[)(STEDH\s+(?:de\s+\d+\s+de\s+\w+\s+de\s+\d+\s+)?(?:Asunto\s+)?([A-ZÁÉÍÓÚa-záéíóú\s]+c\.\s+[A-ZÁÉÍÓÚa-záéíóú\s]+))(?!\))', _sub_tedh, texto)

        # 3. Enriquecer Tribunal Supremo (STS xxx/yyyy)
        def _sub_sts(m):
            full = m.group(0)
            num = m.group(2) if len(m.groups()) >= 2 and m.group(2) else m.group(1)
            url = generar_enlace_cendoj(f"STS {num or full}")
            return f"[{full}]({url})"

        texto = re.sub(r'(?<!\[)(STS\s+(\d+/\d+)(?:,\s*de\s*\d+\s*de\s*\w+(?:\s*de\s*\d+)?)?(?:\s*\([^\)]+\))?)(?!\))', _sub_sts, texto)

        # 4. Enriquecer Tribunal Constitucional (STC xxx/yyyy)
        def _sub_stc(m):
            full = m.group(0)
            num = m.group(2) if len(m.groups()) >= 2 and m.group(2) else m.group(1)
            url = generar_enlace_tc(num or full)
            return f"[{full}]({url})"

        texto = re.sub(r'(?<!\[)(STC\s+(\d+/\d+)(?:,\s*de\s*\d+\s*de\s*\w+(?:\s*de\s*\d+)?)?)(?!\))', _sub_stc, texto)
    except Exception as e:
        print(f"[Aviso Enriquecedor Citas] {e}")

    return texto

MODELOS_CANDIDATOS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.7-flash",
    "gemini-3.6-flash"
]

def obtener_enlace_exacto_articulo(norma: str, articulo: str, url_existente: str) -> str:
    """Asegura que el enlace al BOE o CENDOJ vaya directamente al artículo específico con anchor #a<num>."""
    if "boe.es" in url_existente:
        # Extraer el número de artículo si existe
        match = re.search(r'\b(?:art[íi]culo|art\.?)\s*(\d+)', articulo.lower())
        if match:
            num = match.group(1)
            # Si no tiene ya el anchor
            if "#" not in url_existente:
                return f"{url_existente}#a{num}"
    elif not url_existente or url_existente == "https://www.boe.es":
        return generar_enlace_directo_boe(norma, articulo)
    return url_existente

def consultar_ammayia(pregunta: str, historial: Optional[List[Dict[str, Any]]] = None, modelo: Optional[str] = None) -> Dict[str, Any]:
    """
    Ejecuta el pipeline RAG conversacional completo de AmmayIA con máxima profundidad analítica y enlaces directos a cada artículo.
    """
    # 1. Recuperar contexto jurídico del Vector Store
    documentos_recuperados = vector_store.busqueda_hibrida(pregunta, top_k=5)

    # 2. Construir bloque de contexto con enlaces exactos
    contexto_texto = "=== FUENTES LEGALES Y DOCTRINALES OFICIALES DISPONIBLES ===\n\n"
    fuentes_citadas = []

    for idx, doc in enumerate(documentos_recuperados, start=1):
        url_exacta = obtener_enlace_exacto_articulo(doc["norma"], doc["articulo"], doc["url_boe"])
        
        contexto_texto += f"[{idx}] {doc['norma']} - {doc['articulo']} (Materia: {doc['materia']})\n"
        contexto_texto += f"URL Directa Oficial al Artículo: {url_exacta}\n"
        contexto_texto += f"Texto Legal / Fundamentos:\n{doc['contenido']}\n\n"
        
        fuentes_citadas.append({
            "id": idx,
            "norma": doc["norma"],
            "articulo": doc["articulo"],
            "materia": doc["materia"],
            "url": url_exacta,
            "es_jurisprudencia": doc.get("es_jurisprudencia", False)
        })

    prompt_actual = (
        f"{contexto_texto}\n"
        f"=== CONSULTA DEL JURISTA ===\n"
        f"{pregunta}\n\n"
        f"Emite tu dictamen exhaustivo, minucioso, profundo y extensamente fundamentado en derecho español, citando las leyes con sus enlaces exactos:"
    )

    # 3. Llamar a la API de Google Gemini
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    
    if not api_key:
        return {
            "respuesta": (
                f"⚖️ **Dictamen Jurídico de AmmayIA (Modo Contextual RAG)**\n\n"
                f"📌 **Conclusión Preliminar:**\n"
                f"Respecto a su consulta sobre *'{pregunta}'*, se han identificado las disposiciones y precedentes normativos aplicables en el ordenamiento jurídico español.\n\n"
                f"📜 **Normativa Aplicable Identificada:**\n"
                + "\n".join([f"- **{f['norma']} ({f['articulo']}):** [Consultar artículo en BOE/CENDOJ]({f['url']})" for f in fuentes_citadas])
                + f"\n\n💡 *Para activar el análisis profundo con Gemini Pro, añade tu `GEMINI_API_KEY` en el archivo .env.*"
            ),
            "fuentes": fuentes_citadas,
            "modelo": "RAG-Local-Fallback"
        }

    try:
        client = genai.Client(api_key=api_key)
        
        # 4. Construir historial de mensajes limpio (evitando turnos consecutivos del mismo rol)
        contents = []
        if historial and isinstance(historial, list):
            ultimo_rol = None
            for msg in historial:
                if not isinstance(msg, dict):
                    continue
                raw_content = msg.get("content", "")
                if isinstance(raw_content, dict):
                    raw_content = json.dumps(raw_content, ensure_ascii=False)
                elif not isinstance(raw_content, str):
                    raw_content = str(raw_content)

                raw_content = raw_content.strip()
                if not raw_content:
                    continue

                rol_raw = msg.get("role", "").lower()
                rol = "user" if rol_raw in ["user", "usuario", "letrado", "abogado"] else "model"

                # Evitar duplicar la pregunta actual si venía en el historial
                if rol == "user" and raw_content == pregunta.strip():
                    continue

                # Si hay dos roles iguales seguidos, omitir para no romper la alternancia
                if rol == ultimo_rol and contents:
                    continue

                contents.append(types.Content(role=rol, parts=[types.Part.from_text(text=raw_content)]))
                ultimo_rol = rol

        # Agregar el turno actual con el contexto RAG inyectado
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt_actual)]))

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_AMMAIA,
            temperature=0.2, # Baja temperatura para máxima precisión y fidelidad legal
            top_p=0.95,
            max_output_tokens=8192 # Permitir dictámenes extensos y exhaustivos sin cortes
        )

        # Probar modelo solicitado con fallback a la lista de candidatos
        modelos_a_probar = [modelo] if modelo else []
        for m in MODELOS_CANDIDATOS:
            if m not in modelos_a_probar:
                modelos_a_probar.append(m)

        ultimo_error = None
        for mod in modelos_a_probar:
            try:
                response = client.models.generate_content(
                    model=mod,
                    contents=contents,
                    config=config
                )
                if response and response.text:
                    texto_final = enriquecer_citas_en_texto(str(response.text))
                    return {
                        "respuesta": texto_final,
                        "fuentes": fuentes_citadas,
                        "modelo": mod
                    }
            except Exception as ex:
                ultimo_error = ex
                continue

        raise ultimo_error or Exception("No se pudo conectar con los modelos de Gemini.")

    except Exception as e:
        print(f"[AmmaIA RAG Error] {e}")
        return {
            "respuesta": f"❌ Error al consultar el modelo de IA: {str(e)}. Verifique su conexión y API Key.",
            "fuentes": fuentes_citadas,
            "modelo": modelo or "gemini-2.5-flash"
        }

# Alias para compatibilidad
consultar_ammaia = consultar_ammayia

