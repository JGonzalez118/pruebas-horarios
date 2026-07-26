import numpy as np
from ga.chromosome import CodificadorHorario, SENTINEL


class MotorGenetico:
    def __init__(
        self,
        codificador: CodificadorHorario,
        calculador,
        tamanio_poblacion: int = 80,
        generaciones: int = 300,
        tasa_mutacion: float = 0.05,
        elitismo: int = 4,
        seed: int = 42,
    ):
        self.cod = codificador
        self.fit = calculador
        self.tam = tamanio_poblacion
        self.gens = generaciones
        self.tasa_mutacion = tasa_mutacion
        self.elitismo = elitismo
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    def ejecutar(self) -> tuple[np.ndarray, float, dict]:
        poblacion = self.cod.generar_poblacion(self.tam, seed=42)
        historial = []
        gen_final = 0

        for gen in range(self.gens):
            gen_final = gen
            fitness = self.fit.evaluar_poblacion(poblacion)

            orden = np.argsort(-fitness)
            poblacion = poblacion[orden]
            fitness = fitness[orden]
            historial.append(float(fitness[0]))

            if fitness[0] >= 0.999:
                break

            nueva_poblacion = [poblacion[i] for i in range(self.elitismo)]

            while len(nueva_poblacion) < self.tam:
                p1 = self._seleccion_torneo(poblacion, fitness)
                p2 = self._seleccion_torneo(poblacion, fitness)
                h1, h2 = self._cruce(p1, p2)
                h1 = self._mutar(h1)
                h2 = self._mutar(h2)
                nueva_poblacion.extend([h1, h2])

            poblacion = np.array(nueva_poblacion[: self.tam])

        fitness_final = self.fit.evaluar_poblacion(poblacion)
        mejor_idx = int(np.argmax(fitness_final))

        return poblacion[mejor_idx], float(fitness_final[mejor_idx]), {
            "generaciones_ejecutadas": gen_final + 1,
            "historial_fitness": historial,
        }

    # ------------------------------------------------------------------
    def _seleccion_torneo(self, poblacion, fitness, k: int = 3):
        idxs = self.rng.integers(0, len(poblacion), size=k)
        mejor = idxs[np.argmax(fitness[idxs])]
        return poblacion[mejor]

    def _cruce(self, p1: np.ndarray, p2: np.ndarray):
        """
        Cruce de un punto sobre el eje de cargas académicas. Como cada
        fila es autocontenida (patrón + sus sub-sesiones), cortar entre
        filas nunca deja un gen a medio construir.
        """
        n_cargas = p1.shape[0]
        if n_cargas < 2:
            return p1.copy(), p2.copy()
        punto = self.rng.integers(1, n_cargas)
        h1 = np.vstack([p1[:punto], p2[punto:]])
        h2 = np.vstack([p2[:punto], p1[punto:]])
        return h1, h2

    def _mutar(self, individuo: np.ndarray) -> np.ndarray:
        nuevo = individuo.copy()

        for i, carga in enumerate(self.cod.cargas):
            if self.rng.random() >= self.tasa_mutacion:
                continue

            tipo = self.rng.choice(["patron_completo", "una_subsesion"])

            if tipo == "patron_completo":
                n_patrones = len(carga.patrones_posibles)
                patron_idx = int(self.rng.integers(0, n_patrones))
                nuevo[i] = np.full(nuevo.shape[1], SENTINEL, dtype=np.int32)
                nuevo[i, 0] = patron_idx
                patron = carga.patrones_posibles[patron_idx]
                for k in range(len(patron)):
                    slots = self.cod.slots_validos[i][patron_idx][k]
                    base = 1 + k * 3
                    if len(slots) == 0:
                        nuevo[i, base:base + 3] = [SENTINEL, SENTINEL, self.rng.integers(0, self.cod.n_aulas)]
                        continue
                    idx = self.rng.integers(0, len(slots))
                    dia, bloque_orden = slots[idx]
                    nuevo[i, base:base + 3] = [dia, bloque_orden, self.rng.integers(0, self.cod.n_aulas)]

            else:
                patron_idx = int(nuevo[i, 0])
                patron_idx = max(0, min(patron_idx, len(carga.patrones_posibles) - 1))
                patron = carga.patrones_posibles[patron_idx]
                if not patron:
                    continue
                k = int(self.rng.integers(0, len(patron)))
                slots = self.cod.slots_validos[i][patron_idx][k]
                base = 1 + k * 3
                if len(slots) > 0:
                    idx = self.rng.integers(0, len(slots))
                    dia, bloque_orden = slots[idx]
                    nuevo[i, base] = dia
                    nuevo[i, base + 1] = bloque_orden
                nuevo[i, base + 2] = self.rng.integers(0, self.cod.n_aulas)

        return nuevo
