# AmmaIA — Inteligencia Artificial Jurídica

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LLM: Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%202.5-4285F4.svg?logo=google&logoColor=white)](https://aistudio.google.com/)
[![Deploy: Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg?logo=render&logoColor=white)](https://render.com/)
[![UI: Web & Desktop](https://img.shields.io/badge/UI-Web%20%26%20Desktop-f59e0b)](http://127.0.0.1:8000)

**AmmaIA** es un copiloto y sistema de asistencia jurídica de élite impulsado por Inteligencia Artificial generativa y un motor RAG (*Retrieval-Augmented Generation*) especializado exclusivamente en el **Ordenamiento Jurídico Español y Derecho Europeo**. 

Diseñado para magistrados, fiscales, letrados y despachos jurídicos de máxima exigencia, AmmaIA emite dictámenes forenses exhaustivos con fundamentación legal contrastada, citas directas a artículos del BOE y precedentes judiciales del Tribunal Supremo, Tribunal Constitucional, TEDH y TJUE.

---

## 📑 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Bases de Datos y Fuentes Integradas](#-bases-de-datos-y-fuentes-integradas)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Ejecución en Local](#-instalación-y-ejecución-en-local)
- [Configuración de Variables](#-configuración-de-variables)
- [Despliegue en la Nube (Render)](#-despliegue-en-la-nube-render)
- [Compilación de la App de Escritorio](#-compilación-de-la-app-de-escritorio)
- [Seguridad, Secreto Profesional y RGPD](#-seguridad-secreto-profesional-y-rgpd)
- [Licencia y Autoría](#-licencia-y-autoría)

---

## 🚀 Características Principales

1. **Dictámenes Forenses de Máxima Exhaustividad**: Respuestas estructuradas en 6 secciones (Dictamen Ejecutivo, Exégesis BOE, Jurisprudencia Aplicable, Casuística y Límites, Estrategia Procesal y Borrador de Cláusulas).
2. **Pensamiento CoT Interactivo (*Chain-of-Thought*)**: Muestra en tiempo real el proceso cognitivo de análisis legal con acordeón desplegable estilo Claude / DeepSeek.
3. **Hipervínculos Automáticos y Trazabilidad Total**: Todas las referencias normativas y sentencias citadas se auto-enlazan a sus documentos oficiales (`#a<num>`, CENDOJ, HUDOC o CURIA).
4. **Análisis Forense de Documentos**: Permite adjuntar contratos, demandas y sentencias en formato **PDF, Word (.docx) o TXT** para revisión y extracción de riesgos.
5. **Exportación Oficial de Dictámenes**: Generación instantánea de memorias y dictámenes en **PDF con membrete formal** (ReportLab) y **Word (.docx)** editable.
6. **Sincronización Diaria con el BOE**: Demonio en segundo plano que monitoriza y analiza las nuevas leyes publicadas en el Boletín Oficial del Estado.
7. **Panel Maestro de Administración e Inspector RAW**: Visualización de métricas en tiempo real, gestión de cuotas VIP, auditoría con secreto profesional, bans por IP/HWID y exportación RAW JSON.
8. **Derecho al Olvido (RGPD Art. 17)**: Función de eliminación definitiva e irreversible de cuenta y datos para el usuario y moderadores.
9. **Doble Modalidad (Web App & Desktop WebView)**: Funciona como aplicación web moderna en el navegador y como software de escritorio nativo con aceleración por hardware.

---

## 🏛️ Bases de Datos y Fuentes Integradas

| Organismo / Base de Datos | Cobertura Documental | Acceso Oficial |
| :--- | :--- | :--- |
| **📜 BOE & Códigos Consolidados** | Constitución, Código Penal, Código Civil, LEC, LECrim, ET, etc. | [boe.es](https://www.boe.es) |
| **🏛️ CENDOJ / CGPJ** | Tribunal Supremo (Salas 1ª, 2ª, 3ª y 4ª), Audiencias Provinciales y TSJ | [CENDOJ Jurisprudencia](https://www.poderjudicial.es/cgpj/es/Servicios/Jurisprudencia/Buscador-Fondo-Documental-Jurisprudencia/) |
| **🇪🇺 TEDH (HUDOC & HUDOC-SPA)** | Tribunal Europeo de Derechos Humanos (Gran Sala y Salas) | [HUDOC ECHR](https://hudoc.echr.coe.int/spa) |
| **🇪🇺 TJUE (CURIA)** | Tribunal de Justicia de la Unión Europea y Tribunal General | [CURIA TJUE](https://curia.europa.eu/site/) |
| **⚖️ Tribunal Constitucional** | Sentencias del TC (STC), Autos y Recursos de Inconstitucionalidad | [HJ Constitucional](https://hj.tribunalconstitucional.es) |

---

## 🏗 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    AmmaIA Presentation Layer                │
│    • Web Client (Vanilla JS, CSS3 Cósmico, Marked.js)       │
│    • Desktop Engine (PyWebView Native Window + HWID Bridge) │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│    FastAPI Backend Core      │ │     Generadores Forenses   │
│  - Autenticación JWT / RGPD  │ │  - ReportLab PDF Engine    │
│  - Control de Cuotas Diarias │ │  - Python-docx Builder     │
│  - Panel Maestro & RAW Dump  │ │  - File Ingestion Pipeline │
└──────────────┬───────────────┘ └────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Motor RAG Multijurisdiccional              │
│  - Búsqueda Híbrida Vectorial + TF-IDF (Leyes & Códigos)    │
│  - Resolutor Inteligente CENDOJ / HUDOC / CURIA / BOE       │
│  - Demonio de Auto-Sincronización Matutina del BOE          │
│  - Inferencia LLM: Google Gemini 2.5 Flash (8.192 tokens)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Estructura del Proyecto

```
AmmaIA/
├── backend/                  # Servidor API FastAPI y motor RAG
│   └── app/
│       ├── api/              # Rutas de autenticación, chat, administración y BOE
│       ├── auth/             # Seguridad JWT, hashing bcrypt y control de sesiones
│       ├── database/         # Repositorio SQLite (usuarios, cuotas, bans, chats)
│       └── rag/              # Vector store, scrapers CENDOJ/BOE y generadores PDF
├── desktop/                  # Cliente nativo de escritorio (PyWebView)
│   └── main.py
├── data/                     # Base de datos local (ammaia.db) e índices legales
├── web/                      # Interfaz Web interactiva
│   ├── css/styles.css        # Diseño cósmico con modo oscuro y animaciones CoT
│   ├── js/app.js             # Lógica reactiva de chat, visor CoT y modales
│   └── index.html            # Aplicación de una sola página (SPA)
├── .env.example              # Plantilla de variables de entorno públicas
├── .gitignore                # Reglas estrictas de exclusión de secretos y datos
├── render.yaml               # Manifiesto de despliegue automatizado en Render
├── requirements.txt          # Dependencias Python
├── run_backend.py            # Lanzador directo del servidor ASGI
└── README.md                 # Documentación técnica
```

---

## 📋 Requisitos Previos

- **Python**: 3.10 o superior.
- **Clave API de Google Gemini**: Gratuita o de pago en [Google AI Studio](https://aistudio.google.com).
- **Sistema Operativo**: Windows 10/11, macOS o Linux.

---

## ⚙️ Instalación y Ejecución en Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/AmmaIA.git
   cd AmmaIA
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   # En Windows
   python -m venv venv
   .\venv\Scripts\activate

   # En Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno**:
   Copia el archivo de ejemplo y añade tu clave:
   ```bash
   cp .env.example .env
   ```
   Edita `.env` con tu clave de Gemini:
   ```env
   GEMINI_API_KEY=tu_api_key_aqui
   JWT_SECRET=tu_clave_secreta_para_sesiones_jwt
   PORT=8000
   ```

5. **Iniciar el servidor Web**:
   ```bash
   python run_backend.py
   ```
   Abre tu navegador en **http://127.0.0.1:8000**.

6. **(Opcional) Iniciar la App de Escritorio Nativa**:
   ```bash
   python desktop/main.py
   ```

---

## ☁️ Despliegue en la Nube (Render)

AmmaIA está 100% preparado para ser desplegado en **[Render.com](https://render.com)** como servicio web 24/7 sin coste:

1. Sube tu código a GitHub (el `.gitignore` protegerá automáticamente tu clave local).
2. Entra en tu panel de Render y crea un **New Web Service**.
3. Conecta tu repositorio de GitHub.
4. Render detectará automáticamente [`render.yaml`](render.yaml) o puedes configurar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run_backend.py`
5. En la sección **Environment Variables**, añade:
   - `GEMINI_API_KEY` = `tu_clave_de_gemini`
   - `JWT_SECRET` = `tu_clave_jwt`
   - `PORT` = `10000`
6. ¡Tu copiloto jurídico estará disponible públicamente en `https://tu-app.onrender.com`!

---

## 📦 Compilación de la App de Escritorio

Para generar un ejecutable independiente para Windows (`.exe`):

```bash
pip install pyinstaller

pyinstaller --noconfirm --onedir --windowed \
  --name "AmmaIA" \
  --add-data "web;web" \
  --add-data "backend;backend" \
  desktop/main.py
```

---

## 🔒 Seguridad, Secreto Profesional y RGPD

- **Secreto Profesional del Abogado (Art. 542 LOPJ)**: En el panel de auditoría, las consultas de los letrados se mantienen cifradas y protegidas contra inspecciones indebidas.
- **Protección de API Keys**: La clave de inferencia nunca se expone al cliente frontend ni viaja por la red.
- **Hardware-ID (HWID)**: Detección biométrica y de hardware del equipo para aplicar sanciones o políticas de acceso seguras.
- **Derecho al Olvido (RGPD Art. 17)**: Botón de autodestrucción de cuenta que purga de forma irreversible todos los chats y registros asociados.

---

## 👤 Licencia y Autoría

Desarrollado y mantenido por **Lander De Pablos / ldpcicnm2012** ([@LDPCICNM2012](https://github.com/LDPCICNM2012)).

Distribuido bajo la Licencia [MIT](LICENSE).
