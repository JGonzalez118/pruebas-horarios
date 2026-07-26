import numpy as np
import pandas as pd
from models.domain import CargaAcademica, Bloque
from ga.chromosome import SENTINEL, COLS_POR_CARGA

PESOS_DEFAULT = {
    "aula_duplicada":         1000,
    "docente_duplicado":      1000,
    "grupo_dos_clases":       1000,
    "profesor_no_disponible": 1000,
    "misma_materia_mismo_dia": 800,   # dos sub-sesiones de la misma carga el mismo día
    "turno_correcto":          200,
    "horas_equilibradas":       50,
}

RANGOS_TURNO_MINUTOS = {
    "matutino":   (7 * 60, 12 * 60),
    "vespertino": (13 * 60, 18 * 60),
    "nocturno":   (17 * 60, 22 * 60),
}


class CalculadorFitness:
    def __init__(
        self,
        cargas: list[CargaAcademica],
        bloques: list[Bloque],
        restricciones_activas: list[dict],
    ):
        self.cargas = cargas
        self.bloques = {b.orden: b for b in bloques}
        self.pesos = self._resolver_pesos(restricciones_activas)
        self.activas = {r["codigo"] for r in restricciones_activas}

    def _resolver_pesos(self, restricciones: list[dict]) -> dict:
        pesos = PESOS_DEFAULT.copy()
        for r in restricciones:
            peso_custom = r["parametros"].get("peso")
            if peso_custom is not None and r["codigo"] in pesos:
                pesos[r["codigo"]] = peso_custom
        return pesos

    # ------------------------------------------------------------------
    def evaluar_poblacion(self, poblacion: np.ndarray) -> np.ndarray:
        return np.array([self._evaluar_individuo(ind) for ind in poblacion])

    # ------------------------------------------------------------------
    def _expandir_subsesiones(self, individuo: np.ndarray) -> pd.DataFrame:
        """
        Convierte el genoma híbrido en filas planas: una fila por cada
        bloque de hora que ocupa cada sub-sesión activa. Esto es lo que
        alimenta todas las comprobaciones de choques.
        """
        filas = []
        for i, carga in enumerate(self.cargas):
            patron_idx = int(individuo[i, 0])
            patron_idx = max(0, min(patron_idx, len(carga.patrones_posibles) - 1))
            patron = carga.patrones_posibles[patron_idx]

            for k, duracion in enumerate(patron):
                base = 1 + k * 3
                dia, bloque_orden, aula_idx = individuo[i, base:base + 3]

                if dia == SENTINEL or bloque_orden == SENTINEL:
                    filas.append({
                        "carga_idx": i, "subsesion": k, "sin_slot": True,
                        "dia": -1, "bloque": -1,
                        "grupo_id": carga.grupo_id, "profesor_id": carga.profesor_id,
                        "materia_id": carga.materia_id, "aula_idx": -1,
                    })
                    continue

                for offset in range(duracion):
                    filas.append({
                        "carga_idx": i, "subsesion": k, "sin_slot": False,
                        "dia": int(dia), "bloque": int(bloque_orden) + offset,
                        "grupo_id": carga.grupo_id, "profesor_id": carga.profesor_id,
                        "materia_id": carga.materia_id, "aula_idx": int(aula_idx),
                        "turno_grupo": carga.turno_grupo,
                    })
        return pd.DataFrame(filas)

    # ------------------------------------------------------------------
    def _evaluar_individuo(self, individuo: np.ndarray) -> float:
        df = self._expandir_subsesiones(individuo)
        penalizacion = 0.0

        sin_slot = df[df.get("sin_slot", False) == True] if "sin_slot" in df.columns else df.iloc[0:0]
        penalizacion += len(sin_slot) * self.pesos["profesor_no_disponible"]

        df_validas = df[df.get("sin_slot", False) == False] if "sin_slot" in df.columns else df

        if df_validas.empty:
            return 1.0 / (1.0 + penalizacion)

        # R1: aula duplicada en (dia, bloque, aula)
        dup_aula = df_validas.duplicated(subset=["dia", "bloque", "aula_idx"], keep=False)
        penalizacion += dup_aula.sum() * self.pesos["aula_duplicada"]

        # R2: docente duplicado en (dia, bloque)
        dup_doc = df_validas.duplicated(subset=["dia", "bloque", "profesor_id"], keep=False)
        penalizacion += dup_doc.sum() * self.pesos["docente_duplicado"]

        # R4: grupo con dos clases al mismo tiempo
        dup_grupo = df_validas.duplicated(subset=["dia", "bloque", "grupo_id"], keep=False)
        penalizacion += dup_grupo.sum() * self.pesos["grupo_dos_clases"]

        # R3: dos sub-sesiones de la MISMA carga académica el mismo día
        por_carga_dia = df_validas.groupby(["carga_idx", "dia"])["subsesion"].nunique()
        choques_mismo_dia = (por_carga_dia > 1).sum()
        penalizacion += choques_mismo_dia * self.pesos["misma_materia_mismo_dia"]

        # R-NE: turno correcto según el grupo
        if "turno_correcto" in self.activas:
            penalizacion += self._penalizar_turno(df_validas)

        # R-NE: horas equilibradas por grupo entre días
        if "horas_equilibradas" in self.activas:
            penalizacion += self._penalizar_equilibrio(df_validas)

        return 1.0 / (1.0 + penalizacion)

    # ------------------------------------------------------------------
    def _penalizar_turno(self, df: pd.DataFrame) -> float:
        penalizacion = 0.0
        for _, fila in df.drop_duplicates(subset=["carga_idx", "subsesion"]).iterrows():
            bloque = self.bloques.get(fila["bloque"])
            if bloque is None:
                continue
            minutos = bloque.hora_inicio.hour * 60 + bloque.hora_inicio.minute
            rango = RANGOS_TURNO_MINUTOS.get(str(fila["turno_grupo"]).lower())
            if rango and not (rango[0] <= minutos <= rango[1]):
                penalizacion += self.pesos["turno_correcto"]
        return penalizacion

    def _penalizar_equilibrio(self, df: pd.DataFrame) -> float:
        penalizacion = 0.0
        horas_por_grupo_dia = df.groupby(["grupo_id", "dia"]).size()
        for grupo_id in df["grupo_id"].unique():
            valores = horas_por_grupo_dia.get(grupo_id)
            if valores is None or len(valores) < 2:
                continue
            promedio = valores.mean()
            desequilibrio = (valores - promedio).abs().sum()
            penalizacion += desequilibrio * self.pesos["horas_equilibradas"]
        return penalizacion
