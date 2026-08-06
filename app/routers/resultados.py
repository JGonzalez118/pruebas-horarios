from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_connection
from auth import obtener_usuario_actual, verificar_acceso_facultad

router = APIRouter(prefix="/resultados", tags=["Resultados"])

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles",
        4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}


def _con_nombre_dia(filas):
    for fila in filas:
        fila["dia_nombre"] = DIAS.get(fila["dia"], str(fila["dia"]))
    return filas


@router.get("/grupo/{grupo_id}")
def horario_por_grupo(grupo_id: int, corrida_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            mat.nombre AS materia,
            p.nombre AS profesor_nombre, p.apellido AS profesor_apellido,
            a.nombre AS aula,
            ha.dia, TIME_FORMAT(bh.hora_inicio, '%%H:%%i') AS hora_inicio, TIME_FORMAT(bh.hora_fin, '%%H:%%i') AS hora_fin
        FROM horarios_asignados ha
        JOIN carga_academica ca ON ha.carga_academica_id = ca.id
        JOIN materias mat ON ca.materia_id = mat.id
        JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
        JOIN profesores p ON dxp.profesor_id = p.id
        JOIN aulas a ON ha.aula_id = a.id
        JOIN bloques_horarios bh ON ha.bloque_id = bh.id
        WHERE ca.grupo_id = %s AND ha.corrida_generacion_id = %s
        ORDER BY ha.dia, bh.orden
    """, (grupo_id, corrida_id))
    resultado = _con_nombre_dia(cursor.fetchall())
    conn.close()
    return resultado


@router.get("/profesor/{profesor_id}")
def horario_por_profesor(profesor_id: int, corrida_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            g.codigo_grupo, mat.nombre AS materia,
            a.nombre AS aula, ha.dia, TIME_FORMAT(bh.hora_inicio, '%%H:%%i') AS hora_inicio, TIME_FORMAT(bh.hora_fin, '%%H:%%i') AS hora_fin
        FROM horarios_asignados ha
        JOIN carga_academica ca ON ha.carga_academica_id = ca.id
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN materias mat ON ca.materia_id = mat.id
        JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
        JOIN aulas a ON ha.aula_id = a.id
        JOIN bloques_horarios bh ON ha.bloque_id = bh.id
        WHERE dxp.profesor_id = %s AND ha.corrida_generacion_id = %s
        ORDER BY ha.dia, bh.orden
    """, (profesor_id, corrida_id))
    resultado = _con_nombre_dia(cursor.fetchall())
    conn.close()
    return resultado


@router.get("/aula/{aula_id}")
def horario_por_aula(aula_id: int, corrida_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            g.codigo_grupo, mat.nombre AS materia,
            p.nombre AS profesor_nombre, ha.dia, TIME_FORMAT(bh.hora_inicio, '%%H:%%i') AS hora_inicio, TIME_FORMAT(bh.hora_fin, '%%H:%%i') AS hora_fin
        FROM horarios_asignados ha
        JOIN carga_academica ca ON ha.carga_academica_id = ca.id
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN materias mat ON ca.materia_id = mat.id
        JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
        JOIN profesores p ON dxp.profesor_id = p.id
        JOIN bloques_horarios bh ON ha.bloque_id = bh.id
        WHERE ha.aula_id = %s AND ha.corrida_generacion_id = %s
        ORDER BY ha.dia, bh.orden
    """, (aula_id, corrida_id))
    resultado = _con_nombre_dia(cursor.fetchall())
    conn.close()
    return resultado


class EdicionHorario(BaseModel):
    dia: int | None = None
    bloque_id: int | None = None
    aula_id: int | None = None


@router.patch("/{horario_id}")
def editar_horario_manual(
    horario_id: int,
    datos: EdicionHorario,
    usuario: dict = Depends(obtener_usuario_actual),
):
    """
    Mueve una sesión ya generada a otro día/bloque/aula. Solo permitido
    mientras la corrida a la que pertenece siga en estado 'borrador'
    (no se edita algo que ya está 'publicado' -- para eso primero hay
    que despublicar, fuera del alcance de este endpoint por ahora).

    Revalida contra las mismas restricciones esenciales del GA (aula
    duplicada, docente duplicado, grupo con dos clases a la vez), pero
    como una consulta puntual contra el resto de filas de la MISMA
    corrida -- no vuelve a correr el algoritmo genético completo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ha.id, ha.dia, ha.bloque_id, ha.aula_id, ha.estado,
            ha.corrida_generacion_id, ha.carga_academica_id,
            ca.grupo_id, dxp.profesor_id, c.facultad_id
        FROM horarios_asignados ha
        JOIN carga_academica ca ON ha.carga_academica_id = ca.id
        JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
        JOIN grupos g ON ca.grupo_id = g.id
        JOIN carreras c ON g.carrera_id = c.id
        WHERE ha.id = %s
    """, (horario_id,))
    actual = cursor.fetchone()

    if not actual:
        conn.close()
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    verificar_acceso_facultad(usuario, actual["facultad_id"])

    if actual["estado"] != "borrador":
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=f"Solo se pueden editar horarios en estado 'borrador' (este está en '{actual['estado']}')",
        )

    nuevo_dia = datos.dia if datos.dia is not None else actual["dia"]
    nuevo_bloque_id = datos.bloque_id if datos.bloque_id is not None else actual[
        "bloque_id"]
    nuevo_aula_id = datos.aula_id if datos.aula_id is not None else actual["aula_id"]

    cursor.execute("""
        SELECT ha2.id
        FROM horarios_asignados ha2
        JOIN carga_academica ca2 ON ha2.carga_academica_id = ca2.id
        JOIN disponibilidad_x_profesor dxp2 ON ca2.disponibilidad_x_profesor_id = dxp2.id
        WHERE ha2.corrida_generacion_id = %s
          AND ha2.id != %s
          AND ha2.dia = %s
          AND ha2.bloque_id = %s
          AND (ha2.aula_id = %s OR dxp2.profesor_id = %s OR ca2.grupo_id = %s)
    """, (
        actual["corrida_generacion_id"], horario_id,
        nuevo_dia, nuevo_bloque_id,
        nuevo_aula_id, actual["profesor_id"], actual["grupo_id"],
    ))
    conflicto = cursor.fetchone()

    if conflicto:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=(
                "Ese día/bloque genera un choque de aula, docente o grupo "
                "con otra sesión ya existente en este horario."
            ),
        )

    try:
        cursor.execute(
            "UPDATE horarios_asignados SET dia = %s, bloque_id = %s, aula_id = %s WHERE id = %s",
            (nuevo_dia, nuevo_bloque_id, nuevo_aula_id, horario_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"mensaje": "Horario actualizado correctamente"}
