from fastapi import APIRouter, Depends
from database import get_connection
from auth import obtener_usuario_actual
from validaciones import obtener_umbral_calificacion, consultar_candidatos_elegibles

router = APIRouter(prefix="/profesores", tags=["Profesores"])


@router.get("/disponibles")
def profesores_disponibles(
    facultad_id: int,
    periodo_academico_id: int,
    usuario: dict = Depends(obtener_usuario_actual),
):
    """
    Profesores con horas de contrato restantes para este periodo,
    considerando lo YA comprometido en CUALQUIER facultad (no solo la
    que consulta), para que dos coordinadores no sobre-asignen al mismo
    profesor sin saberlo.
    """
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
def profesores_elegibles(
    materia_id: int,
    periodo_academico_id: int,
    usuario: dict = Depends(obtener_usuario_actual),
):
    """
    Filtra por: departamento compatible, créditos suficientes,
    calificación vigente >= umbral global, y horas restantes de
    contrato. Ordenado por calificación descendente (mejor nota primero).

    Usa el mismo motor de validaciones.py que aplica del lado del
    servidor /carga-academica/ al crear una asignación -- este
    endpoint es solo la vista de "sugerencia" para el coordinador.
    """
    conn = get_connection()
    cursor = conn.cursor()
    umbral = obtener_umbral_calificacion(cursor)
    candidatos = consultar_candidatos_elegibles(
        cursor, materia_id, periodo_academico_id)
    conn.close()

    return {
        "materia_id": materia_id,
        "umbral_calificacion_aplicado": umbral,
        "total_candidatos": len(candidatos),
        "candidatos": candidatos,
    }
