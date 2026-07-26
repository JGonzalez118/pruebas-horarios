# from fastapi import APIRouter, HTTPException
# import json
# from app.database import get_connection

# router = APIRouter(prefix="/profesores", tags=["Profesores"])


# def _obtener_umbral_calificacion(cursor) -> float:
#     """
#     Lee el umbral mínimo GLOBAL de calificación desde la tabla
#     `restricciones` (codigo_restriccion = 'calificacion_minima_docente').
#     Esto evita hardcodear el número 70 en el código: si el umbral
#     cambia, se actualiza en la BD y no hay que tocar la API.
#     """
#     cursor.execute("""
#         SELECT parametros FROM restricciones
#         WHERE codigo_restriccion = 'calificacion_minima_docente'
#           AND activo = TRUE
#     """)
#     row = cursor.fetchone()
#     if not row:
#         # Sin restricción configurada: se asume sin mínimo (no recomendado)
#         return 0.0
#     parametros = json.loads(row['parametros']) if isinstance(row['parametros'], str) else row['parametros']
#     return float(parametros.get("minimo", 0))


# @router.get("/elegibles-para-materia")
# def profesores_elegibles(materia_id: int, periodo_academico_id: int):
#     """
#     Lista de profesores que un coordinador puede elegir para dar una
#     materia específica, filtrados por:
#       - Departamento compatible con la materia
#       - Créditos académicos >= créditos mínimos que exige la materia
#       - Calificación VIGENTE en esa materia >= umbral global (restricciones)
#       - Con horas restantes disponibles en su contrato (cruzando TODAS
#         las facultades donde ya esté comprometido este periodo)

#     Ordenado por calificación descendente: el de mejor nota aparece
#     primero, tal como se prioriza en la práctica.
#     """
#     conn = get_connection()
#     cursor = conn.cursor(dictionary=True)

#     umbral = _obtener_umbral_calificacion(cursor)

#     cursor.execute("""
#         SELECT
#             p.id AS profesor_id,
#             p.nombre, p.apellido,
#             p.creditos_academicos,
#             m.creditos_minimos_docente,
#             cdm.calificacion,
#             cdm.fecha_evaluacion,
#             cp.nombre AS tipo_contrato,
#             cp.horas_max_semanales,
#             COALESCE(SUM(ca.horas_semanales), 0) AS horas_comprometidas,
#             (cp.horas_max_semanales - COALESCE(SUM(ca.horas_semanales), 0)) AS horas_restantes
#         FROM materias m
#         JOIN profesores p
#             ON p.departamento_id = m.departamento_id
#            AND p.creditos_academicos >= m.creditos_minimos_docente
#         JOIN calificaciones_docente_materia cdm
#             ON cdm.profesor_id = p.id
#            AND cdm.materia_id = m.id
#            AND cdm.vigente = TRUE
#            AND cdm.calificacion >= %s
#         JOIN disponibilidad_x_profesor dxp
#             ON dxp.profesor_id = p.id
#            AND dxp.periodo_academico_id = %s
#            AND dxp.activo = TRUE
#         JOIN contratos_profesores cp ON dxp.contrato_id = cp.id
#         LEFT JOIN carga_academica ca
#             ON ca.disponibilidad_x_profesor_id = dxp.id
#            AND ca.periodo_academico_id = %s
#         WHERE m.id = %s
#         GROUP BY p.id, cdm.calificacion, cdm.fecha_evaluacion, cp.id, m.creditos_minimos_docente
#         HAVING horas_restantes > 0
#         ORDER BY cdm.calificacion DESC, horas_restantes DESC
#     """, (umbral, periodo_academico_id, periodo_academico_id, materia_id))

#     resultados = cursor.fetchall()

#     return {
#         "materia_id": materia_id,
#         "umbral_calificacion_aplicado": umbral,
#         "total_candidatos": len(resultados),
#         "candidatos": resultados
#     }
