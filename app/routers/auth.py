from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_connection
from auth import verificar_password, crear_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class LoginRequest(BaseModel):
    correo: str
    password: str


@router.post("/login")
def login(datos: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.rol_id, u.password_hash, u.estado_cuenta, d.facultad_id
        FROM usuarios u
        LEFT JOIN departamentos d ON u.departamento_id = d.id
        WHERE u.correo = %s
    """, (datos.correo,))
    usuario = cursor.fetchone()
    conn.close()

    # Mismo mensaje genérico tanto si el correo no existe como si la
    # contraseña es incorrecta, para no filtrar qué correos existen.
    credenciales_invalidas = HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if not usuario:
        raise credenciales_invalidas
    if usuario["estado_cuenta"] != "Activa":
        raise HTTPException(status_code=403, detail="Cuenta inactiva, contacta al administrador")
    if not verificar_password(datos.password, usuario["password_hash"]):
        raise credenciales_invalidas

    token = crear_token(
        usuario_id=usuario["id"],
        rol_id=usuario["rol_id"],
        facultad_id=usuario["facultad_id"],
    )

    return {"access_token": token, "token_type": "bearer"}