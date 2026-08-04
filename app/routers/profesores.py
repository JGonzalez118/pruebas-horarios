import json
from fastapi import APIRouter, Depends
from database import get_connection

from auth import obtener_usuario_actual, verificar_acceso_facultad

router = APIRouter(prefix="/profesores", tags=["Profesores"])


def _obtener_umbral_calificacion(cursor) -> float:
    cursor.execute("""
        SELECT parametros FROM restricciones
        WHERE codigo_restriccion = 'calificacion_minima_docente' AND activo = TRUE
    """)
    row = cursor.fetchone()
    if not row:
        return 0.0
    parametros = json.loads(row["parametros"]) if isinstance(row["parametros"], str) else row["parametros"]
    return float(parametros.get("minimo", 0))


@router.get("/disponibles")
def profesores_disponibles(facultad_id: int, periodo_academico_id: int, usuario: dict = Depends(obtener_usuario_actual)):
    """
    Profesores con horas de contrato restantes para este periodo,
    considerando lo YA comprometido en CUALQUIER facultad (no solo la
    que consulta), para que dos coordinadores no sobre-asignen al mismo
    profesor sin saberlo.
    """

    verificar_acceso_facultad(usuario, facultad_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            p.id AS profesor_id, p.nombre, p.apellido, p.departamento_id,
            p.creditos_academicos,
            cp.nombre AS tipo_contrato, cp.horas_max_semanales,
            COALESCE(SUM(ca.horas_semanales), 0) AS horas_comprometidas,
            (cp.horas_max_semanales - COALESCE(SUM(ca.horas_semanales), 0)) AS horas_restantes,
            COUNT(DISTINCT c.facultad_id) AS facultades_donde_ya_imparte
        FROM disponibilidad_x_profesor dxp
        JOIN profesores p ON dxp.profesor_id = p.id
        JOIN contratos_profesores cp ON dxp.contrato_id = cp.id
        LEFT JOIN carga_academica ca
            ON ca.disponibilidad_x_profesor_id = dxp.id
           AND ca.periodo_academico_id = %s
        LEFT JOIN grupos g ON ca.grupo_id = g.id
        LEFT JOIN carreras c ON g.carrera_id = c.id
        WHERE dxp.periodo_academico_id = %s AND dxp.activo = TRUE
        GROUP BY p.id, cp.id
        HAVING horas_restantes > 0
        ORDER BY horas_restantes DESC
    """, (periodo_academico_id, periodo_academico_id))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


@router.get("/elegibles-para-materia")
def profesores_elegibles(materia_id: int, periodo_academico_id: int):
    """
    Filtra por: departamento compatible, créditos suficientes,
    calificación vigente >= umbral global, y horas restantes de
    contrato. Ordenado por calificación descendente (mejor nota primero).
    """
    conn = get_connection()
    cursor = conn.cursor()
    umbral = _obtener_umbral_calificacion(cursor)

    cursor.execute("""
        SELECT
            p.id AS profesor_id, p.nombre, p.apellido,
            p.creditos_academicos, m.creditos_minimos_docente,
            cdm.calificacion, cdm.fecha_evaluacion,
            cp.nombre AS tipo_contrato, cp.horas_max_semanales,
            COALESCE(SUM(ca.horas_semanales), 0) AS horas_comprometidas,
            (cp.horas_max_semanales - COALESCE(SUM(ca.horas_semanales), 0)) AS horas_restantes
        FROM materias m
        JOIN profesores p
            ON p.departamento_id = m.departamento_id
           AND p.creditos_academicos >= m.creditos_minimos_docente
        JOIN calificaciones_docente_materia cdm
            ON cdm.profesor_id = p.id AND cdm.materia_id = m.id
           AND cdm.vigente = TRUE AND cdm.calificacion >= %s
        JOIN disponibilidad_x_profesor dxp
            ON dxp.profesor_id = p.id AND dxp.periodo_academico_id = %s AND dxp.activo = TRUE
        JOIN contratos_profesores cp ON dxp.contrato_id = cp.id
        LEFT JOIN carga_academica ca
            ON ca.disponibilidad_x_profesor_id = dxp.id AND ca.periodo_academico_id = %s
        WHERE m.id = %s
        GROUP BY p.id, cdm.calificacion, cdm.fecha_evaluacion, cp.id, m.creditos_minimos_docente
        HAVING horas_restantes > 0
        ORDER BY cdm.calificacion DESC, horas_restantes DESC
    """, (umbral, periodo_academico_id, periodo_academico_id, materia_id))

    resultado = cursor.fetchall()
    conn.close()
    return {
        "materia_id": materia_id,
        "umbral_calificacion_aplicado": umbral,
        "total_candidatos": len(resultado),
        "candidatos": resultado,
    }
