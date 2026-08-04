import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from crud_generico import crear_router_crud, _requerir_administrador
from database import get_connection
from auth import obtener_usuario_actual

# activo NO está en PeriodoUpdate a propósito. La regla de negocio es:
# SOLO UN periodo puede estar activo a la vez (es "el periodo en curso"
# que el frontend usa por defecto en selects/dashboards). El schema no
# tiene una constraint de BD que fuerce esa exclusividad, así que se
# aplica en código: el endpoint /periodos-academicos/{id}/activar
# desactiva todos los demás en la MISMA transacción antes de activar
# el elegido, para que nunca queden dos periodos activos a la vez.
#
# IMPORTANTE: 'activo' aquí es solo una bandera de conveniencia para
# UI (qué periodo mostrar por defecto). El resto de la API (generación,
# carga_academica, disponibilidad, resultados) siempre exige que le
# pases periodo_academico_id explícito -- nunca asume "el activo". Por
# eso sí puedes tener corridas o consultas contra un periodo pasado
# aunque ya no sea el "activo".
#
# CÓMO SE LLENA ESTA TABLA en la práctica:
#   1. Al iniciar un nuevo ciclo (ej. "2026-S2"), créalo con
#      POST /periodos-academicos/ (nace con activo=FALSE siempre).
#   2. fecha_inicio / fecha_fin son las fechas reales de calendario
#      del semestre (para referencia, no se usan como filtro en el GA).
#   3. Cuando ese periodo empieza a operar de verdad, se activa con
#      PATCH /periodos-academicos/{id}/activar -- esto automáticamente
#      desactiva cualquier otro periodo que estuviera activo.
#   4. El periodo anterior queda en la tabla con activo=FALSE, pero
#      sigue totalmente consultable (nada se borra).


class PeriodoCreate(BaseModel):
    nombre: str  # Ej: "2026-S1", "2026-Verano"
    fecha_inicio: datetime.date
    fecha_fin: datetime.date


class PeriodoUpdate(BaseModel):
    nombre: str | None = None
    fecha_inicio: datetime.date | None = None
    fecha_fin: datetime.date | None = None


router = crear_router_crud(
    tabla="periodos_academicos",
    prefijo="/periodos-academicos",
    tag="Periodos Académicos",
    modelo_create=PeriodoCreate,
    modelo_update=PeriodoUpdate,
)


# ---------------------------------------------------------------------
# Endpoint dedicado: activación exclusiva (solo un periodo activo a la vez)
# ---------------------------------------------------------------------

@router.patch(
    "/{periodo_id}/activar",
    summary="Marcar este periodo como el activo (desactiva cualquier otro)",
    description=(
        "Solo puede existir un periodo académico activo a la vez. Este "
        "endpoint desactiva automáticamente cualquier otro periodo que "
        "estuviera marcado como activo, y activa el indicado, en una "
        "sola transacción."
    ),
)
def activar_periodo(
    periodo_id: int,
    usuario: dict = Depends(obtener_usuario_actual),
):
    _requerir_administrador(usuario)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM periodos_academicos WHERE id = %s", (periodo_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Periodo no encontrado")

    try:
        cursor.execute("UPDATE periodos_academicos SET activo = FALSE WHERE activo = TRUE")
        cursor.execute("UPDATE periodos_academicos SET activo = TRUE WHERE id = %s", (periodo_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"mensaje": "Periodo activado correctamente", "periodo_academico_id": periodo_id}


@router.get(
    "/activo/actual",
    summary="Obtener el periodo académico actualmente activo",
)
def obtener_periodo_activo(usuario: dict = Depends(obtener_usuario_actual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM periodos_academicos WHERE activo = TRUE LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()
    if not resultado:
        raise HTTPException(status_code=404, detail="No hay ningún periodo académico activo actualmente")
    return resultado