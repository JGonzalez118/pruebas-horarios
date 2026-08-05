import json


def obtener_umbral_calificacion(cursor) -> float:
    cursor.execute("""
        SELECT parametros FROM restricciones
        WHERE codigo_restriccion = 'calificacion_minima_docente' AND activo = TRUE
    """)
    row = cursor.fetchone()
    if not row:
        return 0.0
    parametros = json.loads(row["parametros"]) if isinstance(
        row["parametros"], str) else row["parametros"]
    return float(parametros.get("minimo", 0))


def consultar_candidatos_elegibles(
    cursor,
    materia_id: int,
    periodo_academico_id: int,
    profesor_id: int | None = None,
) -> list[dict]:
    """
    Motor ÚNICO de elegibilidad profesor-materia: departamento, créditos
    académicos, calificación vigente >= umbral global, contrato activo
    para el periodo, y horas restantes de contrato (cruzando TODAS las
    facultades donde el profesor ya esté comprometido).

    - profesor_id=None -> devuelve TODOS los candidatos elegibles.
      Lo usa GET /profesores/elegibles-para-materia.
    - profesor_id=<id> -> filtra a ese único profesor. Lo usa la
      validación server-side al crear/editar carga_academica.

    Es la MISMA consulta en ambos casos -- un cambio en las reglas de
    negocio se aplica automáticamente a los dos endpoints.
    """
    umbral = obtener_umbral_calificacion(cursor)

    filtro_profesor = "AND p.id = %s" if profesor_id is not None else ""
    params = [umbral, periodo_academico_id, periodo_academico_id, materia_id]
    if profesor_id is not None:
        params.append(profesor_id)

    cursor.execute(f"""
        SELECT
            p.id AS profesor_id, p.nombre, p.apellido,
            p.creditos_academicos, m.creditos_minimos_docente,
            cdm.calificacion, cdm.fecha_evaluacion,
            dxp.id AS disponibilidad_x_profesor_id,
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
        {filtro_profesor}
        GROUP BY p.id, cdm.calificacion, cdm.fecha_evaluacion, cp.id, m.creditos_minimos_docente, dxp.id
        HAVING horas_restantes > 0
        ORDER BY cdm.calificacion DESC, horas_restantes DESC
    """, tuple(params))

    return cursor.fetchall()
