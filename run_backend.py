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

    print("[AmmaIA] Iniciando Servidor Backend de AmmaIA...")
    print("[AmmaIA] Web App disponible en: http://127.0.0.1:8000")
    print("[AmmaIA] Documentacion API en: http://127.0.0.1:8000/docs")

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
