import re
import urllib.parse
from typing import List, Dict, Any, Optional

# URLs Oficiales de Bases de Datos Jurisprudenciales
URL_CENDOJ_GENERAL = "https://www.poderjudicial.es/cgpj/es/Servicios/Jurisprudencia/Buscador-Fondo-Documental-Jurisprudencia/"
URL_CENDOJ_SEARCH = "https://www.poderjudicial.es/search/doSearch?query="
URL_HUDOC_GENERAL = "https://hudoc.echr.coe.int/#{\"documentcollectionid2\":[\"GRANDCHAMBER\",\"CHAMBER\"]}"
URL_HUDOC_SPA = "https://hudoc.echr.coe.int/spa#{\"documentcollectionid2\":[\"GRANDCHAMBER\",\"CHAMBER\"]}"
URL_CURIA_GENERAL = "https://curia.europa.eu/site/"
URL_TC_GENERAL = "https://hj.tribunalconstitucional.es"

def generar_enlace_cendoj(termino: str) -> str:
    """Genera enlace directo de búsqueda en el CENDOJ / CGPJ para sentencias del TS, AN, TSJ o AP."""
    if not termino:
        return URL_CENDOJ_GENERAL
    clean = re.sub(r'[\(\),]', '', str(termino)).strip()
    encoded = urllib.parse.quote_plus(clean)
    return f"https://www.poderjudicial.es/search/doSearch?query={encoded}"

def generar_enlace_hudoc(termino: str, en_espanol: bool = True) -> str:
    """Genera enlace de búsqueda en HUDOC (Tribunal Europeo de Derechos Humanos - TEDH)."""
    base = "https://hudoc.echr.coe.int/spa" if en_espanol else "https://hudoc.echr.coe.int"
    if not termino:
        return base
    clean = re.sub(r'^(?:STEDH|TEDH|Sentencia)\s*(?:de\s*\d+\s*de\s*\w+\s*de\s*\d+)?\s*(?:[-–:]\s*)?', '', str(termino), flags=re.IGNORECASE)
    clean = clean.replace("Asunto", "").replace("asunto", "").strip()
    encoded = urllib.parse.quote(clean)
    return f"{base}#{{\"query\":[\"{encoded}\"],\"documentcollectionid2\":[\"GRANDCHAMBER\",\"CHAMBER\"]}}"

def generar_enlace_curia(num_asunto: str) -> str:
    """Genera enlace directo al expediente o sentencia en CURIA (TJUE / Tribunal General de la UE)."""
    if not num_asunto:
        return URL_CURIA_GENERAL
    match = re.search(r'([C|T]-\d+/\d+|\d+/\d+)', str(num_asunto), re.IGNORECASE)
    if match:
        asunto_id = match.group(1).upper()
        return f"https://curia.europa.eu/juris/liste.jsf?num={asunto_id}"
    encoded = urllib.parse.quote_plus(str(num_asunto))
    return f"https://curia.europa.eu/juris/recherche.jsf?language=es&text={encoded}"

def generar_enlace_tc(num_stc: str) -> str:
    """Genera enlace a jurisprudencia del Tribunal Constitucional."""
    if not num_stc:
        return URL_TC_GENERAL
    match = re.search(r'(\d+/\d+)', str(num_stc))
    if match:
        return f"https://hj.tribunalconstitucional.es/es/Resolucion/Buscar?texto={match.group(1)}"
    return URL_TC_GENERAL

def enlazar_jurisprudencia_automatica(cita: str) -> str:
    """Detecta el tipo de tribunal y genera la URL más exacta y directa posible."""
    c_upper = cita.upper()
    if "TJUE" in c_upper or "CURIA" in c_upper or "ASUNTO C-" in c_upper or "ASUNTO T-" in c_upper:
        return generar_enlace_curia(cita)
    elif "TEDH" in c_upper or "HUDOC" in c_upper or "ECHR" in c_upper or "ESTRASBURGO" in c_upper:
        return generar_enlace_hudoc(cita, en_espanol=True)
    elif "STC" in c_upper or "TRIBUNAL CONSTITUCIONAL" in c_upper:
        return generar_enlace_tc(cita)
    else:
        # Por defecto Tribunal Supremo / CENDOJ
        return generar_enlace_cendoj(cita)


# Repositorio Multijurisdiccional Extenso (Tribunal Supremo, TC, TEDH HUDOC y TJUE CURIA)
JURISPRUDENCIA_REPOSITORIO_BASE: List[Dict[str, Any]] = [
    # ── TRIBUNAL SUPREMO: SALA 2ª (PENAL) ──
    {
        "roj": "STS 721/2023",
        "ecli": "ECLI:ES:TS:2023:721",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Penal (Sala 2ª)",
        "fecha": "2023-05-11",
        "recurso": "Recurso de Casación 3412/2021",
        "ponente": "Excmo. Sr. D. Manuel Marchena Gómez",
        "materia": "Penal - Allanamiento de Morada (Art. 202 CP)",
        "resumen": "Doctrina consolidada sobre el concepto jurídico de morada, delimitación del espacio de intimidad y concurrencia de violencia o intimidación en el allanamiento.",
        "fundamentos": "El bien jurídico tutelado por el art. 202 CP es la intimidad personal y familiar (Art. 18.2 CE), abarcando cualquier recinto cerrado donde se desarrolle la vida privada.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2023%3A721"
    },
    {
        "roj": "STS 345/2022",
        "ecli": "ECLI:ES:TS:2022:345",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Penal (Sala 2ª)",
        "fecha": "2022-04-06",
        "recurso": "Recurso de Casación 1980/2020",
        "ponente": "Excmo. Sr. D. Julián Sánchez Melgar",
        "materia": "Penal - Homicidio y Asesinato (Arts. 138 y 139 CP)",
        "resumen": "Distinción dogmática entre homicidio doloso y asesinato: alevosía sobrevenida, proditoria y de desvalimiento.",
        "fundamentos": "La alevosía exige neutralización objetiva de la defensa y búsqueda subjetiva de impunidad.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2022%3A345"
    },
    {
        "roj": "STS 156/2023",
        "ecli": "ECLI:ES:TS:2023:156",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Penal (Sala 2ª)",
        "fecha": "2023-02-14",
        "recurso": "Recurso de Casación 2890/2021",
        "ponente": "Excmo. Sr. D. Antonio del Moral García",
        "materia": "Penal - Legítima Defensa (Art. 20.4 CP)",
        "resumen": "Requisitos de la eximente de legítima defensa: necesidad racional del medio y falta de provocación.",
        "fundamentos": "La necesidad racional del medio atiende a la proporcionalidad ex ante frente a la agresión ilegítima actual o inminente.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2023%3A156"
    },
    {
        "roj": "STS 512/2021",
        "ecli": "ECLI:ES:TS:2021:512",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Penal (Sala 2ª)",
        "fecha": "2021-06-17",
        "recurso": "Recurso de Casación 1120/2019",
        "ponente": "Excmo. Sr. D. Andrés Martínez Arrieta",
        "materia": "Penal - Hurto vs. Robo con Fuerza (Arts. 234 y 238 CP)",
        "resumen": "Límites dogmáticos entre hurto y robo: escalamiento, fractura y uso de llaves falsas.",
        "fundamentos": "La fuerza en las cosas debe ser el medio específico para acceder o extraer el objeto mueble ajeno.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2021%3A512"
    },

    # ── TRIBUNAL SUPREMO: SALA 1ª (CIVIL) ──
    {
        "roj": "STS 1036/2003",
        "ecli": "ECLI:ES:TS:2003:1036",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Civil (Sala 1ª)",
        "fecha": "2003-07-10",
        "recurso": "Recurso de Casación 100/2002",
        "ponente": "Excmo. Sr. D. Xavier O'Callaghan Muñoz",
        "materia": "Civil - Responsabilidad Extracontractual (Art. 1902 CC)",
        "resumen": "Doctrina consolidada sobre la culpa, causalidad adecuada y teoría del riesgo en daños extracontractuales.",
        "fundamentos": "El Art. 1902 CC exige acción/omisión culpable, acreditación de daño indemnizable real y nexo de causalidad directa o eficiente sin interferencia de fuerza mayor o culpa exclusiva de la víctima.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=STS+1036%2F2003"
    },
    {
        "roj": "STS 452/2023",
        "ecli": "ECLI:ES:TS:2023:452",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Civil (Sala 1ª)",
        "fecha": "2023-04-18",
        "recurso": "Recurso de Casación 2155/2019",
        "ponente": "Excmo. Sr. D. Ignacio Sancho Gargallo",
        "materia": "Civil - Cláusulas Abusivas y Contratos Bancarios (Art. 1255 CC / TRLGDCU)",
        "resumen": "Control de transparencia e incorporación de cláusulas suelo y gastos hipotecarios conforme a directivas UE.",
        "fundamentos": "La falta de transparencia material provoca la nulidad de pleno derecho sin posibilidad de moderación judicial.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2023%3A452"
    },

    # ── TRIBUNAL SUPREMO: SALA 4ª (SOCIAL / LABORAL) ──
    {
        "roj": "STS 890/2022",
        "ecli": "ECLI:ES:TS:2022:890",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Social (Sala 4ª)",
        "fecha": "2022-10-14",
        "recurso": "Recurso de Casación para la Unificación de Doctrina 3210/2020",
        "ponente": "Excma. Sra. Dª. María Luisa Segoviano Astaburuaga",
        "materia": "Laboral - Despido Disciplinario y Nulidad (Arts. 54 y 55 ET)",
        "resumen": "Requisitos de la carta de despido, tipicidad de la falta y calificación judicial (procedente, improcedente, nulo).",
        "fundamentos": "La carta de despido delimita estrictamente el objeto del proceso, sin que la empresa pueda alegar hechos sobrevenidos.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2022%3A890"
    },
    {
        "roj": "STS 321/2023",
        "ecli": "ECLI:ES:TS:2023:321",
        "tribunal": "Tribunal Supremo",
        "sala": "Sala de lo Social (Sala 4ª)",
        "fecha": "2023-03-29",
        "recurso": "Recurso de Casación para la Unificación de Doctrina 1450/2021",
        "ponente": "Excmo. Sr. D. Antonio V. Sempere Navarro",
        "materia": "Laboral - Indemnización por Despido Improcedente (Art. 56 ET / Convenio 158 OIT)",
        "resumen": "Posibilidad de indemnizaciones complementarias o disuasorias frente a los topes legales tasados del Estatuto de los Trabajadores.",
        "fundamentos": "Doctrina de la Sala sobre la indemnización tasada legal del Art. 56 ET y los parámetros del Convenio 158 OIT y Carta Social Europea.",
        "url": "https://www.poderjudicial.es/search/doSearch?query=ECLI%3AES%3ATS%3A2023%3A321"
    },

    # ── TRIBUNAL EUROPEO DE DERECHOS HUMANOS (TEDH / HUDOC) ──
    {
        "roj": "STEDH López Ribalda y otros c. España",
        "ecli": "ECLI:CE:ECHR:2019:1017JUD000187413",
        "tribunal": "Tribunal Europeo de Derechos Humanos (TEDH - Gran Sala)",
        "sala": "Gran Sala (Grand Chamber)",
        "fecha": "2019-10-17",
        "recurso": "Demandas nos. 1874/13 y 8567/13",
        "ponente": "Gran Sala del TEDH",
        "materia": "Derechos Humanos - Videovigilancia laboral y Derecho a la Intimidad (Art. 8 CEDH)",
        "resumen": "Juicio de proporcionalidad en la instalación de cámaras ocultas en el puesto de trabajo frente a sospechas fundadas de hurto grave.",
        "fundamentos": "El TEDH estableció que la vigilancia encubierta no vulneró el Art. 8 CEDH al existir sospechas graves de pérdidas económicas, ser temporal, limitada al área de cajas y con acceso restringido a las grabaciones.",
        "url": "https://hudoc.echr.coe.int/spa#{\"query\":[\"Lopez%20Ribalda\"],\"documentcollectionid2\":[\"GRANDCHAMBER\",\"CHAMBER\"]}"
    },
    {
        "roj": "STEDH Morice c. Francia",
        "ecli": "ECLI:CE:ECHR:2015:0423JUD002936910",
        "tribunal": "Tribunal Europeo de Derechos Humanos (TEDH - Gran Sala)",
        "sala": "Gran Sala",
        "fecha": "2015-04-23",
        "recurso": "Demanda no. 29369/10",
        "ponente": "Gran Sala del TEDH",
        "materia": "Derechos Humanos - Libertad de Expresión del Letrado en Sala y Medios (Art. 10 CEDH)",
        "resumen": "Límites de la libertad de expresión de los abogados en defensa de sus clientes y críticas a la administración de justicia.",
        "fundamentos": "Los letrados gozan de un estatuto reforzado de libertad de expresión para defender eficazmente a sus clientes y contribuir a la confianza pública en la justicia.",
        "url": "https://hudoc.echr.coe.int/spa#{\"query\":[\"Morice\"],\"documentcollectionid2\":[\"GRANDCHAMBER\",\"CHAMBER\"]}"
    },
    {
        "roj": "STEDH Golder c. Reino Unido",
        "ecli": "ECLI:CE:ECHR:1975:0221JUD000445170",
        "tribunal": "Tribunal Europeo de Derechos Humanos (TEDH - Pleno)",
        "sala": "Pleno",
        "fecha": "1975-02-21",
        "recurso": "Demanda no. 4451/70",
        "ponente": "Pleno del TEDH",
        "materia": "Derechos Humanos - Derecho de Acceso a un Tribunal y Tutela Judicial Efectiva (Art. 6.1 CEDH)",
        "resumen": "Consagración fundamental del derecho inalienable de acceso a la justicia y asistencia letrada.",
        "fundamentos": "El Art. 6.1 CEDH garantiza el derecho de toda persona a que un tribunal conozca de cualquier reclamación sobre sus derechos y obligaciones civiles.",
        "url": "https://hudoc.echr.coe.int/spa#{\"query\":[\"Golder\"],\"documentcollectionid2\":[\"GRANDCHAMBER\",\"CHAMBER\"]}"
    },

    # ── TRIBUNAL DE JUSTICIA DE LA UNIÓN EUROPEA (TJUE / CURIA) ──
    {
        "roj": "STJUE Asunto C-154/15 Gutiérrez Naranjo",
        "ecli": "ECLI:EU:C:2016:980",
        "tribunal": "Tribunal de Justicia de la Unión Europea (TJUE - Gran Sala)",
        "sala": "Gran Sala",
        "fecha": "2016-12-21",
        "recurso": "Asuntos acumulados C-154/15, C-307/15 y C-308/15",
        "ponente": "TJUE Gran Sala",
        "materia": "Derecho UE - Efectos Retroactivos de la Nulidad de Cláusulas Suelo (Directiva 93/13/CEE)",
        "resumen": "Incompatibilidad de la limitación temporal de efectos retroactivos establecida por el Tribunal Supremo español con el principio de no vinculación.",
        "fundamentos": "El Art. 6.1 de la Directiva 93/13/CEE debe interpretarse en el sentido de que una cláusula abusiva no vincula al consumidor desde su origen, debiendo restituirse la totalidad de las cantidades indebidamente cobradas.",
        "url": "https://curia.europa.eu/juris/liste.jsf?num=C-154/15"
    },
    {
        "roj": "STJUE Asunto C-131/12 Google Spain",
        "ecli": "ECLI:EU:C:2014:317",
        "tribunal": "Tribunal de Justicia de la Unión Europea (TJUE - Gran Sala)",
        "sala": "Gran Sala",
        "fecha": "2014-05-13",
        "recurso": "Asunto C-131/12",
        "ponente": "TJUE Gran Sala",
        "materia": "Derecho UE - Derecho al Olvido y Protección de Datos Personales (Directiva 95/46/CE / RGPD)",
        "resumen": "Responsabilidad de los motores de búsqueda en el tratamiento de datos y derecho de los ciudadanos a la desindexación.",
        "fundamentos": "El gestor de un motor de búsqueda está obligado a eliminar de la lista de resultados enlaces a páginas web que contengan información lesiva u obsoleta sobre una persona.",
        "url": "https://curia.europa.eu/juris/liste.jsf?num=C-131/12"
    },
    {
        "roj": "STJUE Asuntos acumulados C-59/22 a C-159/22",
        "ecli": "ECLI:EU:C:2024:149",
        "tribunal": "Tribunal de Justicia de la Unión Europea (TJUE - Sala 6ª)",
        "sala": "Sala Sexta",
        "fecha": "2024-02-22",
        "recurso": "Asuntos acumulados C-59/22, C-110/22 y C-159/22",
        "ponente": "TJUE Sala 6ª",
        "materia": "Derecho UE - Abuso de Contratación Temporal en el Sector Público (Acuerdo Marco CES, UNICE y CEEP)",
        "resumen": "Doctrina sobre la fijeza e indemnizaciones a empleados públicos interinos frente a sucesivas relaciones de servicio temporal abusivas.",
        "fundamentos": "El Acuerdo Marco sobre el trabajo de duración determinada se opone a normativas nacionales que no contemplen medidas efectivas ni sanciones disuasorias frente a los abusos en la interinidad pública.",
        "url": "https://curia.europa.eu/juris/liste.jsf?num=C-59/22"
    },

    # ── TRIBUNAL CONSTITUCIONAL (TC) ──
    {
        "roj": "STC 292/2000",
        "ecli": "ECLI:ES:TC:2000:292",
        "tribunal": "Tribunal Constitucional",
        "sala": "Pleno",
        "fecha": "2000-11-30",
        "recurso": "Recurso de Inconstitucionalidad 1463/1993",
        "ponente": "Excmo. Sr. D. Tomás S. Vives Antón",
        "materia": "Constitucional - Derecho Fundamental a la Protección de Datos (Art. 18.4 CE)",
        "resumen": "Autonomía dogmática del derecho a la autodeterminación informativa frente a la intimidad clásica del Art. 18.1 CE.",
        "fundamentos": "El Art. 18.4 CE garantiza el poder de control y disposición sobre los propios datos personales frente al uso de la informática.",
        "url": "https://hj.tribunalconstitucional.es/es/Resolucion/Buscar?texto=292/2000"
    }
]

def buscar_jurisprudencia_cendoj(termino: str) -> List[Dict[str, Any]]:
    """Busca precedentes coincidentes en el repositorio multijurisdiccional de AmmaIA."""
    t_lower = termino.lower()
    coincidencias = []
    
    for doc in JURISPRUDENCIA_REPOSITORIO_BASE:
        materia = doc.get("materia", "").lower()
        resumen = doc.get("resumen", "").lower()
        fundamentos = doc.get("fundamentos", "").lower()
        roj = doc.get("roj", "").lower()

        if any(w in materia or w in resumen or w in fundamentos or w in roj for w in t_lower.split()):
            coincidencias.append(doc)

    return coincidencias
