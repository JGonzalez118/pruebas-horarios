import json
from fastapi import APIRouter
from pydantic import BaseModel

from database import get_connection

router = APIRouter(prefix="/restricciones", tags=["Restricciones"])


class RestriccionIn(BaseModel):
    codigo_restriccion: str
    nombre: str
    descripcion: str | None = None
    tipo: str  # "dura" | "blanda"
    parametros: dict = {}
    activo: bool = True


@router.get("/")
def listar():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restricciones ORDER BY id")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


@router.post("/")
def crear(restriccion: RestriccionIn):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO restricciones
        (codigo_restriccion, nombre, descripcion, tipo, parametros, activo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        restriccion.codigo_restriccion, restriccion.nombre,
        restriccion.descripcion, restriccion.tipo,
        json.dumps(restriccion.parametros), restriccion.activo,
    ))
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return {"id": nuevo_id, "mensaje": "Restricción creada."}


@router.patch("/{restriccion_id}/toggle")
def alternar_activo(restriccion_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE restricciones SET activo = NOT activo WHERE id = %s",
        (restriccion_id,),
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Estado actualizado."}


@router.patch("/{restriccion_id}/peso")
def actualizar_peso(restriccion_id: int, peso: float):
    """
    Actualiza solo el peso dentro del JSON de parametros, sin tocar el
    resto de la configuración de la restricción.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT parametros FROM restricciones WHERE id = %s", (restriccion_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Restricción no encontrada."}

    parametros = json.loads(row["parametros"]) if row["parametros"] else {}
    parametros["peso"] = peso

    cursor2 = conn.cursor()
    cursor2.execute(
        "UPDATE restricciones SET parametros = %s WHERE id = %s",
        (json.dumps(parametros), restriccion_id),
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Peso actualizado.", "parametros": parametros}
