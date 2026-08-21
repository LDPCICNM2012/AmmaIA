import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Configuración del Servidor y Seguridad
APP_NAME = "AmmaIA - Inteligencia Artificial Jurídica"
VERSION = "1.0.0"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Clave secreta para JWT (sesiones seguras)
JWT_SECRET = os.getenv("JWT_SECRET", "ammaia_legal_secure_jwt_secret_key_2026_super_safe")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 30  # 30 días de sesión

# Conexión a Base de Datos Cloud Supabase Propia de AmmaIA
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://duskzcakagxsujvfnfln.supabase.co/rest/v1").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("SUPABASE_KEY", "sb_publishable_7WGpzEI0PI6AMkpDPs5y1w_WbPaQP81"))

# Rutas de configuración y secretos locales
USER_CONFIG_DIR = Path.home() / ".ammaia"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.json"

def _obtener_gemini_key() -> str:
    """Obtiene la clave API de Gemini desde .env, variables de entorno o ~/.ammaia/config.json."""
    # 1. Variable de entorno directa o cargada desde .env
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key

    # 2. Archivo de configuración persistente en el directorio del usuario ~/.ammaia/config.json
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                key_local = data.get("gemini_key") or data.get("GEMINI_API_KEY", "")
                if key_local:
                    return str(key_local).strip()
        except Exception:
            pass

    return ""

# API Keys de Inteligencia Artificial
GEMINI_API_KEY = _obtener_gemini_key()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Modelo de IA predeterminado
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL = "text-embedding-004"

# Cuotas y Límites de Uso
FREE_DAILY_MESSAGE_LIMIT = 5  # 5 mensajes al día para usuarios gratuitos
# Los usuarios con is_premium=True tienen consultas ILIMITADAS

# Administradores con acceso total y privilegios automáticos
ADMIN_EMAILS = [
    "admin@ammaia.com",
    "admin@ammayia.com",
    "lander@ammaia.com",
    "soporte@ammaia.com",
]

# Rutas de almacenamiento de datos
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ammaia.db"
VECTOR_DIR = DATA_DIR / "vector_index"
LEGAL_DOCS_DIR = DATA_DIR / "legal_docs"

# Asegurar directorios
DATA_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DIR.mkdir(parents=True, exist_ok=True)
LEGAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
