import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from ..database.db import obtener_usuario_por_id

security_bearer = HTTPBearer(auto_error=False)

def crear_token_jwt(user_data: Dict[str, Any]) -> str:
    payload = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "nombre": user_data["nombre"],
        "rol": user_data.get("rol", "Abogado"),
        "is_premium": user_data.get("is_premium", False),
        "is_admin": user_data.get("is_admin", False),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decodificar_token_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(status_code=401, detail="No se proporcionó token de autenticación.")
    
    token = credentials.credentials
    payload = decodificar_token_jwt(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado. Inicia sesión de nuevo.")
    
    user_id = int(payload.get("sub", 0))
    user = obtener_usuario_por_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado en la base de datos.")
    
    return user

def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren privilegios de Administrador.")
    return user
