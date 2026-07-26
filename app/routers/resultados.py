from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/resultados", tags=["Resultados"])

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}


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