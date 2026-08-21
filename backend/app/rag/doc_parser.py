import io
from typing import Optional
from pypdf import PdfReader
from docx import Document

def extraer_texto_de_archivo(archivo_bytes: bytes, nombre_archivo: str) -> str:
    """
    Extrae el texto limpio de un archivo adjunto (PDF, DOCX, TXT, JSON).
    """
    ext = nombre_archivo.split(".")[-1].lower() if "." in nombre_archivo else ""

    if ext == "pdf":
        try:
            reader = PdfReader(io.BytesIO(archivo_bytes))
            textos = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt and txt.strip():
                    textos.append(f"--- [Página {i+1}] ---\n{txt.strip()}")
            return "\n\n".join(textos)
        except Exception as e:
            return f"[Error extrayendo texto del PDF '{nombre_archivo}': {e}]"

    elif ext in ["docx", "doc"]:
        try:
            doc = Document(io.BytesIO(archivo_bytes))
            parrafos = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(parrafos)
        except Exception as e:
            return f"[Error extrayendo texto del documento Word '{nombre_archivo}': {e}]"

    elif ext in ["txt", "json", "md", "csv", "xml"]:
        try:
            return archivo_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return archivo_bytes.decode("latin-1", errors="ignore")

    else:
        # Fallback texto plano
        try:
            return archivo_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return f"[Formato de archivo '{nombre_archivo}' no soportado para extracción de texto]."
