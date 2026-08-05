import time
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from database import get_connection
from auth import obtener_usuario_actual, verificar_acceso_facultad
from ga.loader import DataLoader
from ga.chromosome import CodificadorHorario
from ga.fitness import CalculadorFitness
from ga.engine import MotorGenetico
from writer import GuardadorResultados

router = APIRouter(prefix="/generacion", tags=["Generación GA"])


class SolicitudGeneracion(BaseModel):
    facultad_id: int
    periodo_academico_id: int
    tamanio_poblacion: int = 80
    generaciones: int = 300
    tasa_mutacion: float = 0.05


def _ejecutar_ga_en_segundo_plano(corrida_id: int, solicitud: SolicitudGeneracion, usuario_id: int | None):
    """
    Corre en un hilo del threadpool de FastAPI, DESPUÉS de que la
    respuesta HTTP ya se envió al cliente. Usa su PROPIA conexión a la
    BD (nunca reutilices la conexión del request original acá: para
    cuando esto se ejecuta, esa conexión del request ya pudo cerrarse).
    """
    conn = get_connection()
    writer = GuardadorResultados(conn)

    try:
        loader = DataLoader(conn)
        loader.archivar_borradores_facultad(
            solicitud.facultad_id, solicitud.periodo_academico_id)

        cargas = loader.cargar_carga_academica_facultad(
            solicitud.facultad_id, solicitud.periodo_academico_id)
        if not cargas:
            raise ValueError(
                "No hay carga académica para esa facultad/periodo.")

        bloques = loader.cargar_bloques()
        aulas = loader.cargar_aulas_facultad(solicitud.facultad_id)
        restricciones = loader.cargar_restricciones_activas()
        ocupacion_previa = loader.cargar_ocupacion_actual_profesores(
            solicitud.periodo_academico_id)

        codificador = CodificadorHorario(
            cargas, bloques, aulas, ocupacion_previa)
        calculador = CalculadorFitness(cargas, bloques, restricciones)
        motor = MotorGenetico(
            codificador, calculador,
            tamanio_poblacion=solicitud.tamanio_poblacion,
            generaciones=solicitud.generaciones,
            tasa_mutacion=solicitud.tasa_mutacion,
        )

        inicio = time.time()
        mejor_genoma, mejor_fitness, meta = motor.ejecutar()
        duracion = time.time() - inicio

        writer.marcar_exitosa(
            corrida_id, mejor_genoma, codificador, solicitud.periodo_academico_id,
            duracion_segundos=duracion,
            iteraciones=meta["generaciones_ejecutadas"],
            fitness_final=mejor_fitness,
        )

    except Exception as e:
        writer.marcar_fallida(corrida_id, str(e))
    finally:
        conn.close()


@router.post("/ejecutar")
def ejecutar_generacion(
    solicitud: SolicitudGeneracion,
    background_tasks: BackgroundTasks,
    usuario: dict = Depends(obtener_usuario_actual),
):
    verificar_acceso_facultad(usuario, solicitud.facultad_id)

    conn = get_connection()
    writer = GuardadorResultados(conn)
    corrida_id = writer.crear_corrida_pendiente(
        solicitud.periodo_academico_id, usuario["usuario_id"])
    conn.close()

    background_tasks.add_task(
        _ejecutar_ga_en_segundo_plano, corrida_id, solicitud, usuario["usuario_id"]
    )

    return {
        "corrida_generacion_id": corrida_id,
        "estado": "procesando",
        "mensaje": "La generación se está ejecutando en segundo plano. "
                   "Consulta GET /generacion/corridas/{id} para ver el progreso.",
    }


@router.get("/corridas")
def listar_corridas(periodo_academico_id: int, usuario: dict = Depends(obtener_usuario_actual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, fecha_ejecucion, algoritmo_usado, duracion_segundos,
               iteraciones, fitness_final, estado
        FROM corridas_generacion
        WHERE periodo_academico_id = %s
        ORDER BY fecha_ejecucion DESC
    """, (periodo_academico_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


@router.get("/corridas/{corrida_id}")
def obtener_corrida(corrida_id: int, usuario: dict = Depends(obtener_usuario_actual)):
    """
    Endpoint de polling: el frontend llama esto cada 2-3 segundos
    mientras estado == 'procesando', y deja de preguntar cuando cambia
    a 'exitoso' o 'fallido'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, periodo_academico_id, fecha_ejecucion, algoritmo_usado,
               duracion_segundos, iteraciones, fitness_final, estado, mensaje_error
        FROM corridas_generacion
        WHERE id = %s
    """, (corrida_id,))
    resultado = cursor.fetchone()
    conn.close()
    if not resultado:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    return resultado
