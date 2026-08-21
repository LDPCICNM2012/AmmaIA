from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from ..database.db import crear_usuario, autenticar_usuario, obtener_estado_cuota, eliminar_usuario_db
from ..auth.security import crear_token_jwt, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])

class RegistroRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: Optional[str] = "Abogado"
    hwid: Optional[str] = ""

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    hwid: Optional[str] = ""

@router.post("/registro")
def endpoint_registro(req: RegistroRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    ok, msg, user_data = crear_usuario(
        email=req.email,
        password=req.password,
        nombre=req.nombre,
        rol=req.rol or "Abogado",
        hwid=req.hwid or "",
        ip=client_ip
    )
    if not ok or not user_data:
        raise HTTPException(status_code=400, detail=msg)

    token = crear_token_jwt(user_data)
    cuota = obtener_estado_cuota(user_data["id"], user_data["is_premium"])
    
    return {
        "success": True,
        "token": token,
        "usuario": user_data,
        "cuota": cuota,
        "mensaje": msg
    }

@router.post("/login")
def endpoint_login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    ok, msg, user_data = autenticar_usuario(
        email=req.email,
        password=req.password,
        hwid=req.hwid or "",
        ip=client_ip
    )
    if not ok or not user_data:
        raise HTTPException(status_code=401, detail=msg)

    token = crear_token_jwt(user_data)
    cuota = obtener_estado_cuota(user_data["id"], user_data["is_premium"])

    return {
        "success": True,
        "token": token,
        "usuario": user_data,
        "cuota": cuota,
        "mensaje": msg
    }

@router.get("/me")
def endpoint_me(user: Dict[str, Any] = Depends(get_current_user)):
    cuota = obtener_estado_cuota(user["id"], user["is_premium"])
    return {
        "usuario": user,
        "cuota": cuota
    }

@router.delete("/eliminar-mi-cuenta")
def endpoint_eliminar_mi_cuenta(user: Dict[str, Any] = Depends(get_current_user)):
    """Permite al usuario autenticado eliminar definitivamente su cuenta (Derecho al Olvido RGPD Art. 17)."""
    ok = eliminar_usuario_db(user["id"])
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo eliminar la cuenta.")
    return {
        "success": True,
        "mensaje": "Tu cuenta y todos tus dictámenes han sido eliminados definitivamente del servidor."
    }
