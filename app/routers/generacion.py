import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_connection
from ga.loader import DataLoader
from ga.chromosome import CodificadorHorario
from ga.fitness import CalculadorFitness
from ga.engine import MotorGenetico
from writer import GuardadorResultados

router = APIRouter(prefix="/generacion", tags=["Generación GA"])


class SolicitudGeneracion(BaseModel):
    facultad_id: int
    periodo_academico_id: int
    usuario_id: int | None = None
    tamanio_poblacion: int = 80
    generaciones: int = 300
    tasa_mutacion: float = 0.05


@router.post("/ejecutar")
def ejecutar_generacion(solicitud: SolicitudGeneracion):
    conn = get_connection()
    loader = DataLoader(conn)

    # 1. Limpiar corridas 'borrador' anteriores de ESTA facultad, para
    #    no auto-bloquearse contra su propia corrida vieja.
    loader.archivar_borradores_facultad(solicitud.facultad_id, solicitud.periodo_academico_id)

    # 2. Cargar todo lo necesario
    cargas = loader.cargar_carga_academica_facultad(
        solicitud.facultad_id, solicitud.periodo_academico_id
    )
    if not cargas:
        raise HTTPException(404, "No hay carga académica para esa facultad/periodo.")

    bloques = loader.cargar_bloques()
    aulas = loader.cargar_aulas_facultad(solicitud.facultad_id)
    restricciones = loader.cargar_restricciones_activas()
    ocupacion_previa = loader.cargar_ocupacion_actual_profesores(solicitud.periodo_academico_id)

    # 3. Codificar, evaluar, evolucionar
    codificador = CodificadorHorario(cargas, bloques, aulas, ocupacion_previa)
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

    # 4. Guardar
    guardador = GuardadorResultados(conn)
    corrida_id = guardador.guardar(
        genoma=mejor_genoma,
        codificador=codificador,
        periodo_id=solicitud.periodo_academico_id,
        usuario_id=solicitud.usuario_id,
        duracion_segundos=duracion,
        iteraciones=meta["generaciones_ejecutadas"],
    )

    conn.close()

    return {
        "corrida_generacion_id": corrida_id,
        "fitness_final": mejor_fitness,
        "generaciones_ejecutadas": meta["generaciones_ejecutadas"],
        "duracion_segundos": round(duracion, 2),
        "cargas_academicas_procesadas": len(cargas),
    }


@router.get("/corridas")
def listar_corridas(periodo_academico_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, fecha_ejecucion, algoritmo_usado, duracion_segundos,
               iteraciones, estado
        FROM corridas_generacion
        WHERE periodo_academico_id = %s
        ORDER BY fecha_ejecucion DESC
    """, (periodo_academico_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado
