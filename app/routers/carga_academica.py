from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_connection
from auth import obtener_usuario_actual, verificar_acceso_facultad, ROL_ADMINISTRADOR
from validaciones import consultar_candidatos_elegibles

router = APIRouter(prefix="/carga-academica", tags=["Carga Académica"])


class CargaAcademicaCreate(BaseModel):
    grupo_id: int
    materia_id: int
    periodo_academico_id: int
    profesor_id: int
    horas_semanales: int


class CargaAcademicaUpdate(BaseModel):
    profesor_id: int | None = None
    horas_semanales: int | None = None


# ---------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------

def _resolver_facultad_de_grupo(cursor, grupo_id: int) -> int:
    cursor.execute("""
        SELECT c.facultad_id
        FROM grupos g
        JOIN carreras c ON g.carrera_id = c.id
        WHERE g.id = %s
    """, (grupo_id,))
    fila = cursor.fetchone()
    if not fila:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return fila["facultad_id"]


def _validar_y_resolver_profesor(
    cursor, profesor_id: int, materia_id: int, periodo_id: int,
    horas_semanales: int, excluir_carga_id: int | None = None,
) -> int:
    """
    Corre la MISMA lógica de /profesores/elegibles-para-materia
    (validaciones.consultar_candidatos_elegibles), filtrada a un único
    profesor, y además valida que las horas solicitadas quepan en su
    capacidad restante. Lanza 422 con el motivo si no califica.
    Retorna el disponibilidad_x_profesor_id ya resuelto, listo para
    guardar en carga_academica.
    """
    candidatos = consultar_candidatos_elegibles(
        cursor, materia_id, periodo_id, profesor_id=profesor_id)

    if not candidatos:
        raise HTTPException(
            status_code=422,
            detail=(
                "El profesor no es elegible para esta materia: revisa "
                "departamento, créditos académicos, calificación vigente, "
                "o si tiene contrato activo para este periodo."
            ),
        )

    candidato = candidatos[0]
    horas_restantes = candidato["horas_restantes"]

    if excluir_carga_id is not None:
        cursor.execute(
            "SELECT horas_semanales FROM carga_academica "
            "WHERE id = %s AND disponibilidad_x_profesor_id = %s",
            (excluir_carga_id, candidato["disponibilidad_x_profesor_id"]),
        )
        fila_actual = cursor.fetchone()
        if fila_actual:
            horas_restantes += fila_actual["horas_semanales"]

    if horas_semanales > horas_restantes:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El profesor solo tiene {horas_restantes} hora(s) semanales "
                f"disponibles en su contrato, y se solicitaron {horas_semanales}."
            ),
        )

    return candidato["disponibilidad_x_profesor_id"]


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@router.get("/")
def listar_carga_academica(
    grupo_id: int | None = None,
    periodo_academico_id: int | None = None,
    usuario: dict = Depends(obtener_usuario_actual),
):
    conn = get_connection()
    cursor = conn.cursor()

    condiciones, params = [], []
    if grupo_id is not None:
        condiciones.append("ca.grupo_id = %s")
        params.append(grupo_id)
    if periodo_academico_id is not None:
        condiciones.append("ca.periodo_academico_id = %s")
        params.append(periodo_academico_id)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT ca.id, ca.grupo_id, ca.materia_id, ca.horas_semanales,
               ca.periodo_academico_id, dxp.profesor_id, c.facultad_id
        FROM carga_academica ca
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN carreras c ON g.carrera_id = c.id
        JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
        {where}
        ORDER BY ca.id
    """, tuple(params))
    filas = cursor.fetchall()
    conn.close()

    if usuario["rol_id"] != ROL_ADMINISTRADOR:
        filas = [f for f in filas if f["facultad_id"]
                 == usuario["facultad_id"]]

    return filas


@router.get("/{carga_id}")
def obtener_carga_academica(carga_id: int, usuario: dict = Depends(obtener_usuario_actual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.*, c.facultad_id
        FROM carga_academica ca
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN carreras c ON g.carrera_id = c.id
        WHERE ca.id = %s
    """, (carga_id,))
    fila = cursor.fetchone()
    conn.close()

    if not fila:
        raise HTTPException(
            status_code=404, detail="Carga académica no encontrada")
    verificar_acceso_facultad(usuario, fila["facultad_id"])
    return fila


@router.post("/")
def crear_carga_academica(
    datos: CargaAcademicaCreate,
    usuario: dict = Depends(obtener_usuario_actual),
):
    conn = get_connection()
    cursor = conn.cursor()

    facultad_id = _resolver_facultad_de_grupo(cursor, datos.grupo_id)
    verificar_acceso_facultad(usuario, facultad_id)

    dxp_id = _validar_y_resolver_profesor(
        cursor, datos.profesor_id, datos.materia_id,
        datos.periodo_academico_id, datos.horas_semanales,
    )

    cursor.execute(
        "SELECT id FROM carga_academica WHERE grupo_id = %s AND materia_id = %s AND periodo_academico_id = %s",
        (datos.grupo_id, datos.materia_id, datos.periodo_academico_id),
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=409, detail="Ya existe carga académica para ese grupo, materia y periodo")

    try:
        cursor.execute("""
            INSERT INTO carga_academica
            (grupo_id, materia_id, disponibilidad_x_profesor_id, periodo_academico_id, horas_semanales)
            VALUES (%s, %s, %s, %s, %s)
        """, (datos.grupo_id, datos.materia_id, dxp_id, datos.periodo_academico_id, datos.horas_semanales))
        conn.commit()
        nuevo_id = cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"id": nuevo_id, "mensaje": "Carga académica creada correctamente"}


@router.patch("/{carga_id}")
def actualizar_carga_academica(
    carga_id: int,
    datos: CargaAcademicaUpdate,
    usuario: dict = Depends(obtener_usuario_actual),
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ca.*, dxp.profesor_id AS profesor_actual, c.facultad_id
        FROM carga_academica ca
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN carreras c ON g.carrera_id = c.id
        JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
        WHERE ca.id = %s
    """, (carga_id,))
    actual = cursor.fetchone()
    if not actual:
        conn.close()
        raise HTTPException(
            status_code=404, detail="Carga académica no encontrada")

    verificar_acceso_facultad(usuario, actual["facultad_id"])

    nuevo_profesor_id = datos.profesor_id if datos.profesor_id is not None else actual[
        "profesor_actual"]
    nuevas_horas = datos.horas_semanales if datos.horas_semanales is not None else actual[
        "horas_semanales"]

    dxp_id = _validar_y_resolver_profesor(
        cursor, nuevo_profesor_id, actual["materia_id"],
        actual["periodo_academico_id"], nuevas_horas,
        excluir_carga_id=carga_id,
    )

    try:
        cursor.execute(
            "UPDATE carga_academica SET disponibilidad_x_profesor_id = %s, horas_semanales = %s WHERE id = %s",
            (dxp_id, nuevas_horas, carga_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"mensaje": "Carga académica actualizada correctamente"}


@router.delete("/{carga_id}")
def eliminar_carga_academica(carga_id: int, usuario: dict = Depends(obtener_usuario_actual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.facultad_id
        FROM carga_academica ca
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN carreras c ON g.carrera_id = c.id
        WHERE ca.id = %s
    """, (carga_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        raise HTTPException(
            status_code=404, detail="Carga académica no encontrada")
    verificar_acceso_facultad(usuario, fila["facultad_id"])

    try:
        cursor.execute(
            "DELETE FROM carga_academica WHERE id = %s", (carga_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "mensaje": (
            "Carga académica eliminada. Si ya existían horarios generados "
            "para esta asignación, también se eliminaron (ON DELETE CASCADE)."
        )
    }
