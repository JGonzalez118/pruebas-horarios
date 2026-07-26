"""
Patrones válidos para partir 'horas_semanales' de una materia en
sesiones. Respetan la restricción esencial 3: un grupo no puede tener
más de una sesión de la misma materia por día, a menos que estén
seguidas y sumen máximo 3 horas.

Por eso ningún patrón excede un bloque de 3 horas seguidas, y cuando
hay más de una sesión, se asume que irán en DÍAS DISTINTOS (el GA
se encarga de eso; el fitness penaliza si dos sesiones de la misma
carga académica caen el mismo día).

MAX_SUBSESIONES define el tamaño fijo de "espacio" que reservamos en
el cromosoma por cada carga académica (ver chromosome.py). El patrón
más largo que tenemos hoy usa 3 sub-sesiones (ej. 2+2+2), así que ese
es el techo.
"""

MAX_SUBSESIONES = 3

PATRONES_POR_HORAS: dict[int, list[list[int]]] = {
    1: [[1]],
    2: [[2], [1, 1]],
    3: [[3], [2, 1], [1, 2]],
    4: [[2, 2], [3, 1], [1, 3]],
    5: [[3, 2], [2, 3], [2, 2, 1]],
    6: [[3, 3], [2, 2, 2]],
}


def patrones_validos(horas_semanales: int) -> list[list[int]]:
    if horas_semanales in PATRONES_POR_HORAS:
        return PATRONES_POR_HORAS[horas_semanales]

    # Fallback para valores no contemplados: bloques de 2 y resto de 1,
    # sin exceder MAX_SUBSESIONES sesiones.
    patron, restante = [], horas_semanales
    while restante > 0 and len(patron) < MAX_SUBSESIONES:
        bloque = min(restante, 2)
        patron.append(bloque)
        restante -= bloque
    if restante > 0:
        # No cabe en MAX_SUBSESIONES sesiones con bloques de máx. 2h.
        # Se acumula todo en la última sesión (caso límite raro).
        patron[-1] += restante
    return [patron]
