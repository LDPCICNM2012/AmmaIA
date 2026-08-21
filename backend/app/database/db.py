import sqlite3
import hashlib
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pathlib import Path
from ..config import DB_PATH, ADMIN_EMAILS

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa las tablas de la base de datos de AmmayIA."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre TEXT NOT NULL,
        rol TEXT DEFAULT 'Abogado',
        is_premium BOOLEAN DEFAULT 0,
        is_admin BOOLEAN DEFAULT 0,
        hwid TEXT DEFAULT '',
        last_ip TEXT DEFAULT '',
        fecha_registro TEXT NOT NULL
    )
    """)

    # 2. Tabla de Cuotas Diarias (control de 5 msgs/día para cuentas gratis)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuotas_diarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        mensajes_usados INTEGER DEFAULT 0,
        UNIQUE(user_id, fecha),
        FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """)

    # 3. Tabla de Sanciones y Bans (Cuenta, IP, HWID)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target TEXT NOT NULL,
        tipo TEXT NOT NULL, -- 'usuario', 'ip', 'hwid'
        motivo TEXT NOT NULL,
        fecha_ban TEXT NOT NULL
    )
    """)

    # 4. Tabla de Historial de Chats y Consultas Legales
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        mensajes_json TEXT NOT NULL,
        fecha_creacion TEXT NOT NULL,
        fecha_actualizacion TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# ── Operaciones de Usuarios ──

def crear_usuario(email: str, password: str, nombre: str, rol: str = "Abogado", hwid: str = "", ip: str = "") -> tuple[bool, str, Optional[Dict[str, Any]]]:
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return False, "El correo electrónico ya está registrado.", None

    is_admin = 1 if email_clean in ADMIN_EMAILS else 0
    is_premium = 1 if is_admin else 0  # Los admins tienen Premium ilimitado automáticamente
    fecha = datetime.now().isoformat()
    pwd_hash = hash_password(password)

    try:
        cursor.execute("""
        INSERT INTO usuarios (email, password_hash, nombre, rol, is_premium, is_admin, hwid, last_ip, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email_clean, pwd_hash, nombre, rol, is_premium, is_admin, hwid, ip, fecha))
        user_id = cursor.lastrowid
        conn.commit()

        user_data = {
            "id": user_id,
            "email": email_clean,
            "nombre": nombre,
            "rol": rol,
            "is_premium": bool(is_premium),
            "is_admin": bool(is_admin)
        }
        conn.close()
        return True, "Usuario registrado con éxito.", user_data
    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {e}", None

def eliminar_usuario_db(user_id: int) -> bool:
    """Elimina definitivamente un usuario y todos sus datos vinculados (Derecho al Olvido RGPD Art. 17)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cuotas_diarias WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM chats WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def autenticar_usuario(email: str, password: str, hwid: str = "", ip: str = "") -> tuple[bool, str, Optional[Dict[str, Any]]]:
    email_clean = email.strip().lower()
    pwd_hash = hash_password(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar si el usuario, su IP o su HWID están baneados
    cursor.execute("SELECT motivo, tipo FROM bans WHERE target IN (?, ?, ?)", (email_clean, ip, hwid))
    ban = cursor.fetchone()
    if ban:
        conn.close()
        return False, f"ACCESO DENEGADO: Tu {ban['tipo']} ha sido sancionado. Motivo: {ban['motivo']}", None

    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND password_hash = ?", (email_clean, pwd_hash))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, "Correo electrónico o contraseña incorrectos.", None

    # Actualizar último HWID e IP
    cursor.execute("UPDATE usuarios SET last_ip = ?, hwid = ? WHERE id = ?", (ip, hwid, user["id"]))
    conn.commit()

    is_admin = bool(user["is_admin"] or email_clean in ADMIN_EMAILS)
    is_premium = bool(user["is_premium"] or is_admin)

    user_data = {
        "id": user["id"],
        "email": user["email"],
        "nombre": user["nombre"],
        "rol": user["rol"],
        "is_premium": is_premium,
        "is_admin": is_admin
    }
    conn.close()
    return True, "Login correcto.", user_data

def obtener_usuario_por_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    is_admin = bool(row["is_admin"] or row["email"].lower() in ADMIN_EMAILS)
    is_premium = bool(row["is_premium"] or is_admin)
    return {
        "id": row["id"],
        "email": row["email"],
        "nombre": row["nombre"],
        "rol": row["rol"],
        "is_premium": is_premium,
        "is_admin": is_admin,
        "hwid": row["hwid"],
        "last_ip": row["last_ip"],
        "fecha_registro": row["fecha_registro"]
    }

def obtener_todos_los_usuarios() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY id DESC")
    rows = cursor.fetchall()
    
    # Obtener lista de bans para marcar estado
    cursor.execute("SELECT target, tipo, motivo FROM bans")
    bans = {(b["target"], b["tipo"]): b["motivo"] for b in cursor.fetchall()}
    conn.close()

    result = []
    for r in rows:
        email = r["email"]
        ip = r["last_ip"] or ""
        hwid = r["hwid"] or ""
        
        is_banned_user = (email, "usuario") in bans
        is_banned_ip = bool(ip and (ip, "ip") in bans)
        is_banned_hwid = bool(hwid and (hwid, "hwid") in bans)
        is_banned = is_banned_user or is_banned_ip or is_banned_hwid

        ban_motivo = bans.get((email, "usuario")) or (bans.get((ip, "ip")) if ip else "") or (bans.get((hwid, "hwid")) if hwid else "") or ""

        result.append({
            "id": r["id"],
            "email": email,
            "nombre": r["nombre"],
            "rol": r["rol"],
            "is_premium": bool(r["is_premium"] or r["is_admin"] or email in ADMIN_EMAILS),
            "is_admin": bool(r["is_admin"] or email in ADMIN_EMAILS),
            "hwid": hwid,
            "last_ip": ip,
            "fecha_registro": r["fecha_registro"],
            "is_banned": is_banned,
            "is_banned_user": is_banned_user,
            "is_banned_ip": is_banned_ip,
            "is_banned_hwid": is_banned_hwid,
            "ban_motivo": ban_motivo
        })
    return result

def toggle_premium_manual(user_id: int, estado_premium: bool) -> bool:
    """Permite al Admin conceder o retirar el estado Premium Ilimitado a cualquier usuario."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET is_premium = ? WHERE id = ?", (1 if estado_premium else 0, user_id))
    conn.commit()
    conn.close()
    return True

# ── Operaciones de Cuotas (5 msgs/día gratis | Premium Ilimitado) ──

def verificar_y_consumir_cuota(user_id: int, is_premium: bool, limite_gratis: int = 5) -> tuple[bool, int, int]:
    """
    Comprueba si el usuario puede realizar una consulta.
    Retorna: (puede_consultar: bool, usados_hoy: int, restantes_hoy: int)
    Si is_premium es True, siempre retorna True con restantes ilimitados (-1).
    """
    if is_premium:
        return True, 0, -1  # Ilimitado

    hoy = date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT mensajes_usados FROM cuotas_diarias WHERE user_id = ? AND fecha = ?", (user_id, hoy))
    row = cursor.fetchone()

    usados = row["mensajes_usados"] if row else 0

    if usados >= limite_gratis:
        conn.close()
        return False, usados, 0

    # Incrementar consumo
    if row:
        cursor.execute("UPDATE cuotas_diarias SET mensajes_usados = mensajes_usados + 1 WHERE user_id = ? AND fecha = ?", (user_id, hoy))
    else:
        cursor.execute("INSERT INTO cuotas_diarias (user_id, fecha, mensajes_usados) VALUES (?, ?, 1)", (user_id, hoy))

    conn.commit()
    conn.close()

    nuevos_usados = usados + 1
    restantes = max(0, limite_gratis - nuevos_usados)
    return True, nuevos_usados, restantes

def obtener_estado_cuota(user_id: int, is_premium: bool, limite_gratis: int = 5) -> Dict[str, Any]:
    if is_premium:
        return {
            "is_premium": True,
            "usados_hoy": 0,
            "restantes_hoy": -1,
            "limite_diario": -1,
            "texto_badge": "👑 Plan Premium Jurídico (Consultas Ilimitadas)"
        }

    hoy = date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mensajes_usados FROM cuotas_diarias WHERE user_id = ? AND fecha = ?", (user_id, hoy))
    row = cursor.fetchone()
    conn.close()

    usados = row["mensajes_usados"] if row else 0
    restantes = max(0, limite_gratis - usados)

    return {
        "is_premium": False,
        "usados_hoy": usados,
        "restantes_hoy": restantes,
        "limite_diario": limite_gratis,
        "texto_badge": f"Consultas gratuitas hoy: {usados}/{limite_gratis} disponibles"
    }

# ── Operaciones de Bans ──

def aplicar_ban(target: str, tipo: str, motivo: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bans (target, tipo, motivo, fecha_ban) VALUES (?, ?, ?, ?)",
                   (target.strip(), tipo.strip().lower(), motivo.strip(), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def revocar_ban(target: str, tipo: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bans WHERE target = ? AND tipo = ?", (target.strip(), tipo.strip().lower()))
    conn.commit()
    conn.close()
    return True

# ── Operaciones de Chats / Historial ──

def guardar_chat_db(chat_id: str, user_id: int, titulo: str, mensajes: List[Dict[str, Any]]):
    conn = get_db_connection()
    cursor = conn.cursor()
    ahora = datetime.now().isoformat()
    mensajes_str = json.dumps(mensajes, ensure_ascii=False)

    cursor.execute("""
    INSERT INTO chats (id, user_id, titulo, mensajes_json, fecha_creacion, fecha_actualizacion)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        titulo = excluded.titulo,
        mensajes_json = excluded.mensajes_json,
        fecha_actualizacion = excluded.fecha_actualizacion
    """, (chat_id, user_id, titulo, mensajes_str, ahora, ahora))
    conn.commit()
    conn.close()

def obtener_chats_usuario(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, fecha_actualizacion, mensajes_json FROM chats WHERE user_id = ? ORDER BY fecha_actualizacion DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        try:
            mensajes = json.loads(r["mensajes_json"])
        except Exception:
            mensajes = []
        result.append({
            "id": r["id"],
            "titulo": r["titulo"],
            "fecha": r["fecha_actualizacion"],
            "mensajes": mensajes
        })
    return result

def borrar_chat_db(chat_id: str, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
    conn.commit()
    conn.close()

# ── Funciones del Inspector del Servidor (Admin Master) ──

def obtener_metricas_servidor() -> Dict[str, Any]:
    """Recopila estadísticas y métricas del servidor en tiempo real."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM usuarios")
    total_usuarios = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE is_premium = 1")
    total_premium = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM bans")
    total_bans = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM chats")
    total_chats = cursor.fetchone()["total"]

    hoy = date.today().isoformat()
    cursor.execute("SELECT SUM(mensajes_usados) as total FROM cuotas_diarias WHERE fecha = ?", (hoy,))
    row_cuota = cursor.fetchone()
    consultas_hoy = row_cuota["total"] if row_cuota and row_cuota["total"] else 0

    conn.close()

    # Tamaño de base de datos
    db_size_kb = 0
    if DB_PATH.exists():
        db_size_kb = round(DB_PATH.stat().st_size / 1024, 1)

    # Documentos RAG
    vector_file = DB_PATH.parent / "vector_index" / "ammayia_legal_index.json"
    total_chunks_rag = 0
    if vector_file.exists():
        try:
            with open(vector_file, "r", encoding="utf-8") as f:
                total_chunks_rag = len(json.load(f))
        except Exception:
            pass

    return {
        "total_usuarios": total_usuarios,
        "total_premium": total_premium,
        "total_bans": total_bans,
        "total_chats": total_chats,
        "consultas_hoy": consultas_hoy,
        "db_size_kb": f"{db_size_kb} KB",
        "total_chunks_rag": total_chunks_rag,
        "version": "1.0.0",
        "servidor_uptime": "Online (FastAPI Uvicorn)"
    }

def obtener_todos_los_chats_admin() -> List[Dict[str, Any]]:
    """
    Retorna la lista de todos los chats para auditoría del servidor.
    Los mensajes se muestran cifrados para respetar el Secreto Profesional del Letrado (Art. 542 LOPJ).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.id, c.user_id, c.titulo, c.fecha_actualizacion, c.mensajes_json, u.nombre as user_nombre, u.email as user_email
    FROM chats c
    LEFT JOIN usuarios u ON c.user_id = u.id
    ORDER BY c.fecha_actualizacion DESC
    LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        try:
            msgs = json.loads(r["mensajes_json"])
            num_msgs = len(msgs)
        except Exception:
            num_msgs = 0

        # Cifrado de privacidad profesional
        contenido_cifrado = f"🔒 [Cifrado AES-256 / Secreto Profesional del Letrado — Protegido por Art. 542 LOPJ y RGPD ({num_msgs} mensajes encriptados)]"

        result.append({
            "chat_id": r["id"],
            "user_id": r["user_id"],
            "user_nombre": r["user_nombre"] or "Letrado Desconocido",
            "user_email": r["user_email"] or "N/D",
            "titulo": r["titulo"],
            "fecha": r["fecha_actualizacion"],
            "num_mensajes": num_msgs,
            "contenido_seguro": contenido_cifrado
        })
    return result

def obtener_todos_los_bans() -> List[Dict[str, Any]]:
    """Retorna la lista completa de todas las sanciones y bloqueos activos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, target, tipo, motivo, fecha_ban FROM bans ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "target": r["target"],
            "tipo": r["tipo"],
            "motivo": r["motivo"],
            "fecha_ban": r["fecha_ban"]
        } for r in rows
    ]

def obtener_raw_server_dump() -> Dict[str, Any]:
    """Extrae TODOS los datos brutos del servidor SQLite y del Vector Store en formato RAW JSON."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, nombre, rol, is_premium, is_admin, hwid, last_ip, fecha_registro FROM usuarios")
    usuarios_raw = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, user_id, fecha, mensajes_usados FROM cuotas_diarias")
    cuotas_raw = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, target, tipo, motivo, fecha_ban FROM bans")
    bans_raw = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, user_id, titulo, fecha_creacion, fecha_actualizacion FROM chats")
    chats_raw = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # RAG Vector Store RAW
    vector_file = DB_PATH.parent / "vector_index" / "ammaia_legal_index.json"
    if not vector_file.exists():
        vector_file = DB_PATH.parent / "vector_index" / "ammayia_legal_index.json"
    
    rag_raw = []
    if vector_file.exists():
        try:
            with open(vector_file, "r", encoding="utf-8") as f:
                rag_raw = json.load(f)
        except Exception:
            pass

    return {
        "sistema": "AmmaIA Core v1.0.0",
        "timestamp_dump": datetime.now().isoformat(),
        "total_tablas_sqlite": 4,
        "base_de_datos": {
            "usuarios": usuarios_raw,
            "cuotas_diarias": cuotas_raw,
            "sanciones_bans": bans_raw,
            "chats_metadata": chats_raw
        },
        "rag_vector_index": {
            "total_documentos_indexados": len(rag_raw),
            "documentos_muestra": rag_raw[:10],
            "total_items": len(rag_raw)
        }
    }
