import datetime
import json
from models.domain import Bloque, Aula, CargaAcademica, DisponibilidadSlot
from ga.patrones import patrones_validos


def _a_time(valor) -> datetime.time:
    """
    pymysql devuelve las columnas TIME como datetime.timedelta (duración
    desde medianoche), mientras que el resto del proyecto trabaja con
    datetime.time (una hora del día). Esta función normaliza cualquiera
    de los dos formatos a datetime.time.
    """
    if isinstance(valor, datetime.time):
        return valor
    if isinstance(valor, datetime.timedelta):
        total_segundos = int(valor.total_seconds())
        horas, resto = divmod(total_segundos, 3600)
        minutos, segundos = divmod(resto, 60)
        return datetime.time(hour=horas % 24, minute=minutos, second=segundos)
    raise TypeError(
        f"No se pudo convertir {valor!r} ({type(valor)}) a datetime.time")


class DataLoader:
    """
    Toda la lectura de sistema_horarios_ga necesaria para armar una
    corrida del GA. Cada método hace UNA consulta clara; nada de ORM
    para mantener control total sobre el SQL en esta fase de pruebas.
    """

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    # ------------------------------------------------------------------
    def cargar_bloques(self) -> list[Bloque]:
        self.cursor.execute("""
            SELECT id, hora_inicio, hora_fin, orden
            FROM bloques_horarios
            ORDER BY orden
        """)
        bloques = []
        for row in self.cursor.fetchall():
            bloques.append(Bloque(
                id=row["id"],
                hora_inicio=_a_time(row["hora_inicio"]),
                hora_fin=_a_time(row["hora_fin"]),
                orden=row["orden"],
            ))
        return bloques

    # ------------------------------------------------------------------
    def cargar_aulas_facultad(self, facultad_id: int) -> list[Aula]:
        self.cursor.execute("""
            SELECT id, facultad_id, capacidad, tipo
            FROM aulas
            WHERE facultad_id = %s AND activo = TRUE
        """, (facultad_id,))
        return [Aula(**row) for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------
    def cargar_carga_academica_facultad(
        self, facultad_id: int, periodo_id: int
    ) -> list[CargaAcademica]:
        """
        Carga académica de TODAS las carreras de la facultad para ese
        periodo. Esta es la unidad que arma una corrida del GA (ver
        recomendación de generar por facultad, no por carrera aislada).
        """
        self.cursor.execute("""
            SELECT
                ca.id,
                ca.grupo_id,
                ca.materia_id,
                ca.disponibilidad_x_profesor_id,
                dxp.profesor_id,
                ca.horas_semanales,
                g.turno AS turno_grupo,
                c.facultad_id
            FROM carga_academica ca
            JOIN grupos g ON ca.grupo_id = g.id
            JOIN carreras c ON g.carrera_id = c.id
            JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
            WHERE c.facultad_id = %s
              AND ca.periodo_academico_id = %s
        """, (facultad_id, periodo_id))

        cargas = []
        for row in self.cursor.fetchall():
            disponibilidad = self._cargar_disponibilidad(
                row["disponibilidad_x_profesor_id"])
            carga = CargaAcademica(
                id=row["id"],
                grupo_id=row["grupo_id"],
                materia_id=row["materia_id"],
                disponibilidad_x_profesor_id=row["disponibilidad_x_profesor_id"],
                profesor_id=row["profesor_id"],
                horas_semanales=row["horas_semanales"],
                turno_grupo=row["turno_grupo"],
                facultad_id=row["facultad_id"],
                disponibilidad=disponibilidad,
            )
            carga.patrones_posibles = patrones_validos(carga.horas_semanales)
            cargas.append(carga)
        return cargas

    # ------------------------------------------------------------------
    def _cargar_disponibilidad(self, dxp_id: int) -> list[DisponibilidadSlot]:
        self.cursor.execute("""
            SELECT dia, bloque_id
            FROM horarios_disponibles
            WHERE disponibilidad_x_profesor_id = %s
        """, (dxp_id,))
        return [DisponibilidadSlot(**row) for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------
    def cargar_restricciones_activas(self) -> list[dict]:
        """Lee la tabla de restricciones configurables (pesos del fitness)."""
        self.cursor.execute("""
            SELECT codigo_restriccion, tipo, parametros
            FROM restricciones
            WHERE activo = TRUE
        """)
        restricciones = []
        for row in self.cursor.fetchall():
            restricciones.append({
                "codigo": row["codigo_restriccion"],
                "tipo": row["tipo"],
                "parametros": json.loads(row["parametros"]) if row["parametros"] else {},
            })
        return restricciones

    # ------------------------------------------------------------------
    def cargar_ocupacion_actual_profesores(self, periodo_id: int) -> dict[int, set[tuple]]:
        """
        Para cada profesor: qué (dia, bloque_id) ya tiene ocupados en
        CUALQUIER facultad para este periodo (corridas 'borrador' o
        'publicado'). Evita que dos coordinadores de facultades
        distintas le asignen al mismo profesor dos clases a la vez.
        """
        self.cursor.execute("""
            SELECT dxp.profesor_id, ha.dia, ha.bloque_id
            FROM horarios_asignados ha
            JOIN carga_academica ca ON ha.carga_academica_id = ca.id
            JOIN disponibilidad_x_profesor dxp ON ca.disponibilidad_x_profesor_id = dxp.id
            WHERE ha.periodo_academico_id = %s
              AND ha.estado IN ('borrador', 'publicado')
        """, (periodo_id,))

        ocupacion: dict[int, set[tuple]] = {}
        for row in self.cursor.fetchall():
            ocupacion.setdefault(row["profesor_id"], set()).add(
                (row["dia"], row["bloque_id"])
            )
        return ocupacion

    # ------------------------------------------------------------------
    def archivar_borradores_facultad(self, facultad_id: int, periodo_id: int):
        """
        Antes de regenerar el horario de una facultad, archiva sus
        borradores anteriores para que no se auto-bloqueen en
        cargar_ocupacion_actual_profesores() en la siguiente corrida.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE horarios_asignados ha
                JOIN carga_academica ca ON ha.carga_academica_id = ca.id
                JOIN grupos g ON ca.grupo_id = g.id
                JOIN carreras c ON g.carrera_id = c.id
                SET ha.estado = 'archivado'
                WHERE c.facultad_id = %s
                AND ha.periodo_academico_id = %s
                AND ha.estado = 'borrador'
            """, (facultad_id, periodo_id))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
