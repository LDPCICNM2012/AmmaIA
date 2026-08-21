import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, VERSION
from .database.db import init_db
from .rag.boe_scheduler import iniciar_sincronizador_automatico, detener_sincronizador_automatico
from .api.auth_routes import router as auth_router
from .api.chat_routes import router as chat_router
from .api.admin_routes import router as admin_router
from .api.boe_routes import router as boe_router

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Motor RAG de Inteligencia Artificial Jurídica especializada en Legislación Española (BOE, Códigos Consolidados, CENDOJ y TC)."
)

# Configuración de CORS para Web App y Desktop Client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Base de Datos y Demonio de Sincronización Diaria del BOE al arrancar
@app.on_event("startup")
def on_startup():
    init_db()
    iniciar_sincronizador_automatico()

@app.on_event("shutdown")
def on_shutdown():
    detener_sincronizador_automatico()

# Registrar Rutas de la API
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(boe_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "app": APP_NAME,
        "version": VERSION,
        "auto_sync_boe": "enabled",
        "rag_sources": ["BOE Diario Automático", "Códigos Consolidados", "CENDOJ (Tribunal Supremo)", "Tribunal Constitucional", "DGT/TEAC"]
    }

# Servir frontend web si existe el directorio
WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
