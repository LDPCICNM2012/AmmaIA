"""
AmmaIA — Desktop Client (Native WebView Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aplicación nativa de escritorio que ejecuta la interfaz
jurídica de AmmaIA con el 100% de la fidelidad visual,
animaciones, modo oscuro cósmico y soporte de hardware.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import os
import time
import threading
import socket
import webview
import requests
from pathlib import Path

# Asegurar codificación UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = int(os.getenv("PORT", 8000))
SERVER_URL = os.getenv("AMMAIA_BACKEND_URL", f"http://127.0.0.1:{PORT}")

# Configurar rutas para que Python encuentre los módulos
desktop_dir = Path(__file__).resolve().parent
project_root = desktop_dir.parent
backend_dir = project_root / "backend"

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

def is_port_in_use(port: int) -> bool:
    """Comprueba si el backend de FastAPI ya está corriendo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_backend():
    """Inicia el servidor backend FastAPI automáticamente en segundo plano si no está activo."""
    if not is_port_in_use(PORT):
        print("[AmmaIA Desktop] Iniciando servidor backend interno...")
        try:
            import uvicorn
            from app.main import app
            config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            # Reintentar con import alternativo
            try:
                import uvicorn
                from backend.app.main import app
                config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
                server = uvicorn.Server(config)
                server.run()
            except Exception as e2:
                print(f"[AmmaIA Desktop Error] No se pudo iniciar el backend: {e2}")

def wait_for_server():
    """Espera a que el servidor esté listo para recibir peticiones."""
    for _ in range(40):
        try:
            r = requests.get(f"{SERVER_URL}/api/health", timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(0.2)
    return False

class AmmaIAApi:
    """Puente nativo entre Python y JavaScript."""
    def get_system_info(self):
        import uuid
        return {
            "platform": sys.platform,
            "hwid": str(uuid.UUID(int=uuid.getnode())),
            "version": "1.0.0"
        }

def main():
    # 1. Iniciar backend en un hilo secundario si no está corriendo
    if not is_port_in_use(PORT):
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        wait_for_server()

    api = AmmaIAApi()

    # 2. Crear ventana nativa de escritorio con la interfaz visual idéntica a la web
    window = webview.create_window(
        title="AmmaIA — Inteligencia Artificial Jurídica",
        url=SERVER_URL,
        width=1360,
        height=860,
        min_size=(980, 640),
        background_color='#050811',
        js_api=api,
        text_select=True
    )

    webview.start(debug=False)

if __name__ == "__main__":
    main()
