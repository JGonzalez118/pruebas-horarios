from ga.chromosome import CodificadorHorario, SENTINEL


class GuardadorResultados:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    def crear_corrida_pendiente(self, periodo_id: int, usuario_id: int | None) -> int:
        """
        Se llama ANTES de correr el GA, para tener un id que devolver
        de inmediato al cliente. Nace en estado 'procesando'.
        """
        self.cursor.execute("""
            INSERT INTO corridas_generacion
            (periodo_academico_id, usuario_id, algoritmo_usado, estado)
            VALUES (%s, %s, %s, 'procesando')
        """, (periodo_id, usuario_id, "GA-Hibrido-NumPy-v1"))
        self.conn.commit()
        return self.cursor.lastrowid

    def marcar_exitosa(
        self, corrida_id: int, genoma, codificador: CodificadorHorario,
        periodo_id: int, duracion_segundos: float, iteraciones: int, fitness_final: float,
    ):
        try:
            self._insertar_horarios(
                genoma, codificador, periodo_id, corrida_id)
            self.cursor.execute("""
                UPDATE corridas_generacion
                SET estado = 'exitoso', duracion_segundos = %s,
                    iteraciones = %s, fitness_final = %s
                WHERE id = %s
            """, (duracion_segundos, iteraciones, fitness_final, corrida_id))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def marcar_fallida(self, corrida_id: int, mensaje_error: str):
        try:
            self.cursor.execute("""
                UPDATE corridas_generacion
                SET estado = 'fallido', mensaje_error = %s
                WHERE id = %s
            """, (mensaje_error[:2000], corrida_id))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def _insertar_horarios(self, genoma, codificador: CodificadorHorario, periodo_id: int, corrida_id: int):
        id_por_orden = {b.orden: b.id for b in codificador.bloques}
        aula_ids = [a.id for a in codificador.aulas]

        registros = []
        for i, carga in enumerate(codificador.cargas):
            patron_idx = int(genoma[i, 0])
            patron_idx = max(
                0, min(patron_idx, len(carga.patrones_posibles) - 1))
            patron = carga.patrones_posibles[patron_idx]

            for k in range(len(patron)):
                base = 1 + k * 3
                dia, bloque_orden, aula_idx = genoma[i, base:base + 3]
                if dia == SENTINEL or bloque_orden == SENTINEL:
                    continue

                bloque_id = id_por_orden.get(int(bloque_orden))
                if bloque_id is None:
                    continue
                aula_id = aula_ids[int(aula_idx)]

                registros.append((
                    carga.id, aula_id, periodo_id, corrida_id,
                    int(dia), bloque_id, "borrador",
                ))

        self.cursor.executemany("""
            INSERT INTO horarios_asignados
            (carga_academica_id, aula_id, periodo_academico_id,
             corrida_generacion_id, dia, bloque_id, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, registros)
