"""
AmmaIA — Módulo de Ingesta y Entrenamiento del RAG Jurídico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este script permite entrenar e indexar nuevas leyes del BOE,
jurisprudencia del CENDOJ, documentos PDF, Word (.docx) o TXT
dentro de la base de datos vectorial de AmmaIA.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
from pathlib import Path

# Asegurar codificación UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Añadir backend al PYTHONPATH
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir / "backend"))

from backend.app.rag.vector_store import vector_store
from backend.app.rag.legal_chunker import chunk_texto_legal
from backend.app.rag.boe_scraper import obtener_leyes_del_dia_xml, ultimo_dia_laboral, CODIGOS_CONSOLIDADOS_MAPA
from backend.app.rag.cendoj_client import JURISPRUDENCIA_REPOSITORIO_BASE

def mostrar_menu():
    print("\n" + "═"*65)
    print("  ⚖️  AMMAIA — ENTRENAMIENTO & INGESTA DEL MOTOR RAG")
    print("═"*65)
    print("  1. 📜 Ingestar / Actualizar BOE del Día")
    print("  2. 🏛️ Ingestar Jurisprudencia de CENDOJ y Tribunal Supremo")
    print("  3. 📂 Ingestar Documento Local (.txt, .docx, .pdf o .json)")
    print("  4. ✍️ Pegar e Ingestar Artículo o Texto Legal Manualmente")
    print("  5. 📊 Ver Estadísticas y Documentos Indexados")
    print("  0. 🚪 Salir")
    print("─"*65)


def ingestar_boe_del_dia():
    fecha = ultimo_dia_laboral()
    print(f"\n[BOE] Consultando sumario oficial del BOE para la fecha: {fecha}...")
    leyes = obtener_leyes_del_dia_xml(fecha)
    
    if not leyes:
        print("[BOE] No se encontraron disposiciones publicadas para esta fecha.")
        return

    print(f"[BOE] {len(leyes)} disposiciones encontradas. Indexando en RAG...")
    nuevos = 0
    for l in leyes:
        titulo = l.get("titulo", "")
        url_web = l.get("url_web", "")
        materia = "Legislación Diaria" if not l.get("es_relevante") else "Legislación Relevante"
        
        vector_store.agregar_documento(
            norma=f"BOE ({fecha})",
            articulo=f"Disposición {l.get('id', '')}",
            contenido=titulo,
            url_boe=url_web,
            materia=materia,
            guardar_disco=False
        )
        nuevos += 1

    vector_store.guardar_en_disco()
    print(f"✅ ¡Éxito! Se han indexado {nuevos} disposiciones del BOE.")


def ingestar_cendoj():
    print("\n[CENDOJ] Indexando repositorio de jurisprudencia y doctrina...")
    for j in JURISPRUDENCIA_REPOSITORIO_BASE:
        vector_store.agregar_documento(
            norma=f"{j['tribunal']} ({j['sala']}) - {j['roj']}",
            articulo=f"Sentencia {j['fecha']} (Rec. {j['recurso']})",
            contenido=f"Resumen: {j['resumen']}\nFundamentos: {j['fundamentos']}",
            url_boe=j["url"],
            materia=j["materia"],
            es_jurisprudencia=True,
            guardar_disco=False
        )
    vector_store.guardar_en_disco()
    print(f"✅ ¡Éxito! Jurisprudencia de CENDOJ y Tribunal Constitucional indexada.")


def ingestar_archivo_local():
    print("\n[Archivo] Introduce la ruta completa del archivo legal:")
    ruta_input = input("Ruta: ").strip().strip('"').strip("'")
    
    if not os.path.exists(ruta_input):
        print("❌ Error: El archivo especificado no existe.")
        return

    path_obj = Path(ruta_input)
    norma_nombre = input("Nombre de la Norma / Sentencia (ej: Ley Orgánica 1/2004 o STS 55/2024): ").strip() or path_obj.stem
    materia = input("Materia jurídica (ej: Penal, Civil, Laboral, Contencioso): ").strip() or "General"
    url_ref = input("Enlace oficial (BOE / CENDOJ / opcional): ").strip() or "https://www.boe.es"

    texto = ""
    ext = path_obj.suffix.lower()

    try:
        if ext == ".txt":
            with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()
        elif ext == ".docx":
            from docx import Document
            doc = Document(path_obj)
            texto = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        else:
            with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()
    except Exception as e:
        print(f"❌ Error leyendo el archivo: {e}")
        return

    if not texto.strip():
        print("❌ El archivo está vacío.")
        return

    print(f"[Chunking] Troceando y estructurando artículos de '{norma_nombre}'...")
    chunks = chunk_texto_legal(texto, norma_nombre=norma_nombre, url_boe=url_ref, materia=materia)

    for ch in chunks:
        vector_store.agregar_documento(
            norma=ch.norma_nombre,
            articulo=ch.articulo_num,
            contenido=ch.contenido,
            url_boe=ch.url_boe,
            materia=ch.materia,
            guardar_disco=False
        )

    vector_store.guardar_en_disco()
    print(f"✅ ¡Éxito! Se han extraído e indexado {len(chunks)} fragmentos/artículos en el RAG.")


def ingestar_texto_manual():
    print("\n[Manual] Ingesta directa de artículo o sentencia:")
    norma = input("Nombre de la ley o tribunal (ej: Código Penal): ").strip()
    art = input("Artículo o Sentencia (ej: Artículo 142 bis o STS 120/2023): ").strip()
    materia = input("Materia (ej: Penal, Civil): ").strip() or "General"
    url = input("URL oficial (BOE/CENDOJ): ").strip() or "https://www.boe.es"
    
    print("Introduce o pega el contenido legal (pulsa Ctrl+Z o Ctrl+D en una línea vacía para terminar):")
    lineas = []
    try:
        while True:
            line = input()
            lineas.append(line)
    except EOFError:
        pass

    contenido = "\n".join(lineas).strip()
    if not contenido:
        print("❌ Contenido vacío.")
        return

    vector_store.agregar_documento(
        norma=norma,
        articulo=art,
        contenido=contenido,
        url_boe=url,
        materia=materia,
        guardar_disco=True
    )
    print(f"✅ ¡Artículo '{norma} - {art}' indexado con éxito en AmmayIA!")


def ver_estadisticas():
    docs = vector_store.documentos
    print("\n" + "─"*55)
    print(f"📊 ESTADÍSTICAS DEL ÍNDICE RAG DE AMMAYIA")
    print("─"*55)
    print(f"• Total de Artículos y Sentencias Indexadas: {len(docs)}")
    
    materias = {}
    for d in docs:
        m = d.get("materia", "General")
        materias[m] = materias.get(m, 0) + 1
        
    print("• Desglose por Materia Jurídica:")
    for mat, count in materias.items():
        print(f"   - {mat}: {count} disposiciones")
    print("─"*55)


def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción (0-5): ").strip()
        
        if opcion == "1":
            ingestar_boe_del_dia()
        elif opcion == "2":
            ingestar_cendoj()
        elif opcion == "3":
            ingestar_archivo_local()
        elif opcion == "4":
            ingestar_texto_manual()
        elif opcion == "5":
            ver_estadisticas()
        elif opcion == "0":
            print("\n👋 ¡Hasta pronto!")
            break
        else:
            print("❌ Opción inválida.")


if __name__ == "__main__":
    main()
