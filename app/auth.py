from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from config import settings

# Roles: coincide con lo insertado en tu tabla `roles` del seed.
# Ajusta estos IDs si en tu BD quedaron en otro orden.
ROL_ADMINISTRADOR = 1
ROL_COORDINADOR = 2

security = HTTPBearer()


def hashear_password(password_plano: str) -> str:
    hash_bytes = bcrypt.hashpw(
        password_plano.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_password(password_plano: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password_plano.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(usuario_id: int, rol_id: int, facultad_id: int | None) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "rol_id": rol_id,
        "facultad_id": facultad_id,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def obtener_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency de FastAPI: decodifica y valida el JWT extraído
    automáticamente del header Authorization por HTTPBearer. Esto es
    lo que hace aparecer el botón "Authorize" en Swagger.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Token inválido o expirado")

    return {
        "usuario_id": int(payload["sub"]),
        "rol_id": payload["rol_id"],
        "facultad_id": payload.get("facultad_id"),
    }


def verificar_acceso_facultad(usuario: dict, facultad_id_solicitada: int):
    """
    Un Administrador puede operar sobre cualquier facultad.
    Un Coordinador solo sobre la suya (la que quedó grabada en su
    token al hacer login).
    """
    if usuario["rol_id"] == ROL_ADMINISTRADOR:
        return
    if usuario["facultad_id"] != facultad_id_solicitada:
        raise HTTPException(
            status_code=403, detail="No tienes permiso sobre esa facultad")
