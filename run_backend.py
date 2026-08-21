import uvicorn
import os
import sys

# Asegurar codificación UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(current_dir, "backend"))

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    is_render = os.getenv("RENDER") is not None

    print(f"[AmmaIA] Iniciando Servidor Backend de AmmaIA en {host}:{port}...")
    print(f"[AmmaIA] Entorno: {'Producción (Render)' if is_render else 'Local'}")

    uvicorn.run("backend.app.main:app", host=host, port=port, reload=not is_render)
