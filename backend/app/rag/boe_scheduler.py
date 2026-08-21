"""
AmmaIA — Sincronizador Automático Diario del BOE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tarea en segundo plano que consulta diariamente el sumario
oficial del BOE a primera hora de la mañana y actualiza el
índice del motor RAG de forma 100% automática sin intervención.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import threading
import time
from datetime import datetime, date
from .boe_scraper import obtener_leyes_del_dia_xml, ultimo_dia_laboral
from .vector_store import vector_store

_cron_activo = False

def sincronizar_boe_ahora():
    """Ejecuta la sincronización inmediata del BOE del día laboral actual."""
    fecha = ultimo_dia_laboral()
    fecha_str = fecha.strftime("%Y-%m-%d")
    print(f"[BOE Auto-Sync] Sincronizando disposiciones oficiales para: {fecha_str}...")

    try:
        leyes = obtener_leyes_del_dia_xml(fecha)
        if not leyes:
            print(f"[BOE Auto-Sync] Sin novedades normativas para {fecha_str}.")
            return 0

        nuevas = 0
        for l in leyes:
            titulo = l.get("titulo", "")
            id_boe = l.get("id", "")
            url_web = l.get("url_web", "")
            es_rel = l.get("es_relevante", False)
            materia = "Legislación BOE Relevante" if es_rel else "Legislación BOE"

            vector_store.agregar_documento(
                norma=f"BOE ({fecha_str})",
                articulo=f"Disposición {id_boe}",
                contenido=titulo,
                url_boe=url_web,
                materia=materia,
                guardar_disco=False
            )
            nuevas += 1

        vector_store.guardar_en_disco()
        print(f"[BOE Auto-Sync] ✅ Sincronización completada: {nuevas} disposiciones incorporadas al RAG.")
        return nuevas
    except Exception as e:
        print(f"[BOE Auto-Sync Error] {e}")
        return 0


def _bucle_demonio_boe():
    """Bucle en segundo plano: comprueba cada 4 horas si hay nuevas leyes publicadas en el BOE."""
    ultima_fecha_sincronizada = None

    while _cron_activo:
        hoy = date.today()
        # Si no hemos sincronizado hoy o es un nuevo día hábil
        if hoy != ultima_fecha_sincronizada:
            sincronizar_boe_ahora()
            ultima_fecha_sincronizada = hoy

        # Esperar 4 horas antes de la siguiente verificación (4 * 3600 segundos)
        for _ in range(4 * 3600):
            if not _cron_activo:
                break
            time.sleep(1)


def iniciar_sincronizador_automatico():
    """Arranca el demonio de sincronización diaria del BOE."""
    global _cron_activo
    if not _cron_activo:
        _cron_activo = True
        hilo = threading.Thread(target=_bucle_demonio_boe, daemon=True, name="AmmaIA_BOE_Daemon")
        hilo.start()
        print("[AmmaIA] 🤖 Demonio de sincronización automática del BOE activo.")


def detener_sincronizador_automatico():
    global _cron_activo
    _cron_activo = False
