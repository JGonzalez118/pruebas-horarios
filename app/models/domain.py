from dataclasses import dataclass, field
import datetime


@dataclass(frozen=True)
class Bloque:
    """Fila de bloques_horarios."""
    id: int
    hora_inicio: datetime.time
    hora_fin: datetime.time
    orden: int


@dataclass(frozen=True)
class Aula:
    """Fila de aulas, ya filtrada por facultad."""
    id: int
    facultad_id: int
    capacidad: int
    tipo: str


@dataclass(frozen=True)
class DisponibilidadSlot:
    """Un (dia, bloque_id) donde el profesor puede dar clase."""
    dia: int          # 1..7
    bloque_id: int


@dataclass
class CargaAcademica:
    """
    Una fila de carga_academica: QUÉ se debe impartir, con el profesor
    YA fijo (decisión del coordinador, no del GA). El GA solo decide
    CUÁNDO (día + bloque) y DÓNDE (aula).
    """
    id: int
    grupo_id: int
    materia_id: int
    disponibilidad_x_profesor_id: int
    profesor_id: int
    horas_semanales: int
    turno_grupo: str
    facultad_id: int
    disponibilidad: list[DisponibilidadSlot] = field(default_factory=list)

    # Se llena en el paso de planificación (ga/patrones.py):
    # todas las formas válidas de partir horas_semanales en sesiones.
    # Ej: horas_semanales=4 -> [[2, 2], [3, 1], [1, 3]]
    patrones_posibles: list[list[int]] = field(default_factory=list)
