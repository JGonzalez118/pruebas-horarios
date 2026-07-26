import numpy as np
from models.domain import CargaAcademica, Bloque, Aula
from ga.patrones import MAX_SUBSESIONES

# Columnas por carga académica: patron_idx + (dia, bloque_orden, aula_idx) * MAX_SUBSESIONES
COLS_POR_CARGA = 1 + MAX_SUBSESIONES * 3
SENTINEL = -1  # marca "sub-sesión no usada" o "sin slot válido"


class CodificadorHorario:
    def __init__(
        self,
        cargas: list[CargaAcademica],
        bloques: list[Bloque],
        aulas: list[Aula],
        ocupacion_previa: dict[int, set] | None = None,
    ):
        self.cargas = cargas
        self.bloques = bloques
        self.aulas = aulas
        self.n_cargas = len(cargas)
        self.n_aulas = len(aulas)
        self.ocupacion_previa = ocupacion_previa or {}

        self._orden_por_id = {b.id: b.orden for b in bloques}
        self._id_por_orden = {b.orden: b.id for b in bloques}

        # slots_validos[i][p][k] -> np.ndarray de (dia, bloque_orden_inicio) válidos
        self.slots_validos: list[list[list[np.ndarray]]] = []
        for carga in cargas:
            self.slots_validos.append(self._slots_para_carga(carga))

    # ------------------------------------------------------------------
    def _slots_para_carga(self, carga: CargaAcademica) -> list[list[np.ndarray]]:
        disponibles = {(s.dia, s.bloque_id) for s in carga.disponibilidad}
        ocupados = self.ocupacion_previa.get(carga.profesor_id, set())
        disponibles -= ocupados

        resultado_por_patron = []
        for patron in carga.patrones_posibles:
            resultado_subsesiones = []
            for duracion in patron:
                resultado_subsesiones.append(
                    self._slots_validos_duracion(disponibles, duracion)
                )
            resultado_por_patron.append(resultado_subsesiones)
        return resultado_por_patron

    def _slots_validos_duracion(self, disponibles: set, duracion: int) -> np.ndarray:
        validos = []
        for (dia, bloque_id) in disponibles:
            orden_inicio = self._orden_por_id[bloque_id]
            ok = True
            for offset in range(duracion):
                bloque_id_actual = self._id_por_orden.get(orden_inicio + offset)
                if bloque_id_actual is None or (dia, bloque_id_actual) not in disponibles:
                    ok = False
                    break
            if ok:
                validos.append((dia, orden_inicio))
        return np.array(validos, dtype=np.int32) if validos else np.empty((0, 2), dtype=np.int32)

    # ------------------------------------------------------------------
    def generar_individuo_aleatorio(self, rng: np.random.Generator) -> np.ndarray:
        genoma = np.full((self.n_cargas, COLS_POR_CARGA), SENTINEL, dtype=np.int32)

        for i, carga in enumerate(self.cargas):
            n_patrones = len(carga.patrones_posibles)
            # Preferir patrones donde TODAS las sub-sesiones tengan slots válidos
            patrones_factibles = [
                p for p in range(n_patrones)
                if all(len(s) > 0 for s in self.slots_validos[i][p])
            ]
            patron_idx = rng.choice(patrones_factibles) if patrones_factibles else rng.integers(0, n_patrones)
            genoma[i, 0] = patron_idx

            patron = carga.patrones_posibles[patron_idx]
            for k in range(len(patron)):
                slots = self.slots_validos[i][patron_idx][k]
                base = 1 + k * 3
                if len(slots) == 0:
                    genoma[i, base:base + 3] = [SENTINEL, SENTINEL, rng.integers(0, self.n_aulas)]
                    continue
                idx = rng.integers(0, len(slots))
                dia, bloque_orden = slots[idx]
                aula_idx = rng.integers(0, self.n_aulas)
                genoma[i, base:base + 3] = [dia, bloque_orden, aula_idx]

        return genoma

    def generar_poblacion(self, tamanio: int, seed: int = 42) -> np.ndarray:
        rng = np.random.default_rng(seed)
        poblacion = np.zeros((tamanio, self.n_cargas, COLS_POR_CARGA), dtype=np.int32)
        for i in range(tamanio):
            poblacion[i] = self.generar_individuo_aleatorio(rng)
        return poblacion
