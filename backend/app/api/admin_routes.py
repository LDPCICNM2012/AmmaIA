from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..auth.security import require_admin
from ..database.db import (
    obtener_todos_los_usuarios,
    toggle_premium_manual,
    aplicar_ban,
    revocar_ban,
    obtener_metricas_servidor,
    obtener_todos_los_chats_admin,
    obtener_todos_los_bans,
    obtener_raw_server_dump,
    eliminar_usuario_db
)

router = APIRouter(prefix="/admin", tags=["Panel Maestro de Administración"])

class TogglePremiumRequest(BaseModel):
    user_id: int
    is_premium: bool

class BanRequest(BaseModel):
    target: str
    tipo: str  # 'usuario', 'ip', 'hwid'
    motivo: str

class UnbanRequest(BaseModel):
    target: str
    tipo: str

@router.get("/metricas")
def endpoint_admin_metricas(admin: Dict[str, Any] = Depends(require_admin)):
    """Retorna métricas globales del servidor en tiempo real."""
    return obtener_metricas_servidor()

@router.get("/raw-dump")
def endpoint_admin_raw_dump(admin: Dict[str, Any] = Depends(require_admin)):
    """Retorna TODOS los datos brutos del servidor (Base de datos SQLite, chats, usuarios, RAG) en RAW JSON."""
    return obtener_raw_server_dump()

@router.get("/usuarios")
def endpoint_admin_usuarios(admin: Dict[str, Any] = Depends(require_admin)):
    """Retorna la lista completa de usuarios con su estado de cuota, IP, HWID y sanciones."""
    usuarios = obtener_todos_los_usuarios()
    return {"usuarios": usuarios}

@router.delete("/usuario/{user_id}")
def endpoint_admin_eliminar_usuario(user_id: int, admin: Dict[str, Any] = Depends(require_admin)):
    """Elimina definitivamente un usuario y todos sus datos vinculados del servidor."""
    ok = eliminar_usuario_db(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no se pudo eliminar.")
    return {
        "success": True,
        "mensaje": f"Usuario ID #{user_id} eliminado definitivamente del sistema."
    }

@router.get("/auditoria-chats")
def endpoint_admin_auditoria_chats(admin: Dict[str, Any] = Depends(require_admin)):
    """Retorna auditoría de consultas registradas (los mensajes están cifrados por secreto profesional)."""
    chats = obtener_todos_los_chats_admin()
    return {"chats": chats}

@router.get("/bans-activos")
def endpoint_admin_bans_activos(admin: Dict[str, Any] = Depends(require_admin)):
    """Retorna lista de todas las sanciones de Cuenta, IP y HWID activas."""
    bans = obtener_todos_los_bans()
    return {"bans": bans}

@router.post("/toggle-premium")
def endpoint_admin_toggle_premium(req: TogglePremiumRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Permite al Admin conceder o revocar el estado Premium Ilimitado a cualquier usuario de forma manual."""
    ok = toggle_premium_manual(req.user_id, req.is_premium)
    estado_str = "Premium Ilimitado ACTIVADO" if req.is_premium else "Premium DESACTIVADO"
    return {
        "success": ok,
        "mensaje": f"Estado actualizado: {estado_str} para el usuario ID {req.user_id}."
    }

@router.post("/ban")
def endpoint_admin_ban(req: BanRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Aplica sanción de Cuenta, IP o HWID en todo el sistema."""
    if req.tipo not in ["usuario", "ip", "hwid"]:
        raise HTTPException(status_code=400, detail="Tipo de ban inválido. Use 'usuario', 'ip' o 'hwid'.")
    
    aplicar_ban(req.target, req.tipo, req.motivo)
    return {
        "success": True,
        "mensaje": f"Sanción aplicada a {req.tipo} '{req.target}'. Motivo: {req.motivo}"
    }

@router.post("/unban")
def endpoint_admin_unban(req: UnbanRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Revoca una sanción activa."""
    revocar_ban(req.target, req.tipo)
    return {
        "success": True,
        "mensaje": f"Sanción revocada para {req.tipo} '{req.target}'."
    }
