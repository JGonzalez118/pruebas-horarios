from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from database import get_connection
from auth import obtener_usuario_actual, hashear_password, ROL_ADMINISTRADOR

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


class UsuarioCreate(BaseModel):
    rol_id: int
    departamento_id: int | None = None
    cedula: str
    nombre: str
    apellido: str
    correo: EmailStr
    password: str


def _requerir_administrador(usuario: dict):
    if usuario["rol_id"] != ROL_ADMINISTRADOR:
        raise HTTPException(
            status_code=403, detail="Solo un administrador puede realizar esta acción")


@router.post("/")
def crear_usuario(
    datos: UsuarioCreate,
    usuario_actual: dict = Depends(obtener_usuario_actual),
):
    _requerir_administrador(usuario_actual)

    conn = get_connection()
    cursor = conn.cursor()

    # Evitar correo o cédula duplicados con un mensaje claro, en vez de
    # dejar que truene el UNIQUE de la BD con un error críptico.
    cursor.execute(
        "SELECT id FROM usuarios WHERE correo = %s OR cedula = %s",
        (datos.correo, datos.cedula),
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=409, detail="Ya existe un usuario con ese correo o cédula")

    password_hash = hashear_password(datos.password)

    try:
        cursor.execute("""
            INSERT INTO usuarios
            (rol_id, departamento_id, cedula, nombre, apellido, correo, password_hash, estado_cuenta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Activa')
        """, (
            datos.rol_id, datos.departamento_id, datos.cedula,
            datos.nombre, datos.apellido, datos.correo, password_hash,
        ))
        conn.commit()
        nuevo_id = cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"id": nuevo_id, "mensaje": "Usuario creado correctamente"}


@router.get("/")
def listar_usuarios(usuario_actual: dict = Depends(obtener_usuario_actual)):
    _requerir_administrador(usuario_actual)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.rol_id, r.nombre_rol, u.departamento_id,
               u.nombre, u.apellido, u.correo, u.estado_cuenta
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        ORDER BY u.id
    """)
    resultado = cursor.fetchall()
    conn.close()
    return resultado
