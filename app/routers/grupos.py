from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from crud_generico import crear_router_crud, _requerir_administrador
from database import get_connection
from auth import obtener_usuario_actual

# carrera_id NO está en GrupoUpdate a propósito: cambiar la carrera de
# un grupo después de creado puede dejar su carga_academica apuntando
# a materias que ya no pertenecen al plan de estudios de la nueva
# carrera. Por eso NO se edita con el PATCH genérico -- solo a través
# de /grupos/{id}/reasignar-carrera, que exige confirmación explícita.
#
# Esta tabla tampoco tiene columna 'activo' en el schema.


class GrupoCreate(BaseModel):
    carrera_id: int
    codigo_grupo: str
    turno: str  # "matutino" | "vespertino" | "nocturno"
    cantidad_estudiantes: int


class GrupoUpdate(BaseModel):
    codigo_grupo: str | None = None
    turno: str | None = None
    cantidad_estudiantes: int | None = None


router = crear_router_crud(
    tabla="grupos",
    prefijo="/grupos",
    tag="Grupos",
    modelo_create=GrupoCreate,
    modelo_update=GrupoUpdate,
    tiene_activo=False,
)


# ---------------------------------------------------------------------
# Endpoint dedicado: reasignar carrera, con advertencia previa
# ---------------------------------------------------------------------

class ReasignarCarreraRequest(BaseModel):
    nueva_carrera_id: int
    confirmar: bool = False


@router.patch(
    "/{grupo_id}/reasignar-carrera",
    summary="Cambiar la carrera de un grupo (requiere confirmación en dos pasos)",
    description=(
        "Paso 1: llama con confirmar=false (o sin el campo). Te devuelve "
        "una advertencia con cuántas filas de carga_academica quedarían "
        "potencialmente inconsistentes, SIN aplicar ningún cambio.\n\n"
        "Paso 2: si el usuario confirma en el frontend, vuelve a llamar "
        "con confirmar=true para aplicar el cambio de verdad."
    ),
)
def reasignar_carrera(
    grupo_id: int,
    datos: ReasignarCarreraRequest,
    usuario: dict = Depends(obtener_usuario_actual),
):
    _requerir_administrador(usuario)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM grupos WHERE id = %s", (grupo_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    cursor.execute("SELECT id FROM carreras WHERE id = %s AND activo = TRUE", (datos.nueva_carrera_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="La carrera destino no existe o está inactiva")

    cursor.execute("SELECT COUNT(*) AS total FROM carga_academica WHERE grupo_id = %s", (grupo_id,))
    afectadas = cursor.fetchone()["total"]

    if not datos.confirmar:
        conn.close()
        return {
            "requiere_confirmacion": True,
            "advertencia": (
                f"Este grupo tiene {afectadas} materia(s) con carga académica "
                f"asignada. Cambiar su carrera puede dejar esas asignaciones "
                f"inconsistentes con el nuevo plan de estudios. Vuelve a "
                f"llamar este endpoint con \"confirmar\": true para aplicar "
                f"el cambio de todos modos."
            ),
            "carga_academica_afectada": afectadas,
        }

    try:
        cursor.execute(
            "UPDATE grupos SET carrera_id = %s WHERE id = %s",
            (datos.nueva_carrera_id, grupo_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "mensaje": "Carrera reasignada correctamente",
        "carga_academica_afectada": afectadas,
    }