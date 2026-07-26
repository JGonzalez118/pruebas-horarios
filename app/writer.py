from ga.chromosome import CodificadorHorario, SENTINEL


class GuardadorResultados:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    def guardar(
        self,
        genoma,
        codificador: CodificadorHorario,
        periodo_id: int,
        usuario_id: int | None,
        duracion_segundos: float,
        iteraciones: int,
    ) -> int:

        self.cursor.execute("""
            INSERT INTO corridas_generacion
            (periodo_academico_id, usuario_id, algoritmo_usado,
             duracion_segundos, iteraciones, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (periodo_id, usuario_id, "GA-Hibrido-NumPy-v1",
              duracion_segundos, iteraciones, "exitoso"))
        corrida_id = self.cursor.lastrowid

        id_por_orden = {b.orden: b.id for b in codificador.bloques}
        aula_ids = [a.id for a in codificador.aulas]

        registros = []
        for i, carga in enumerate(codificador.cargas):
            patron_idx = int(genoma[i, 0])
            patron_idx = max(0, min(patron_idx, len(carga.patrones_posibles) - 1))
            patron = carga.patrones_posibles[patron_idx]

            for k in range(len(patron)):
                base = 1 + k * 3
                dia, bloque_orden, aula_idx = genoma[i, base:base + 3]
                if dia == SENTINEL or bloque_orden == SENTINEL:
                    continue  # sub-sesión sin slot válido, se omite (queda reportada en el fitness)

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

        self.conn.commit()
        return corrida_id
