from pydantic import BaseModel
from crud_generico import crear_router_crud

# facultad_id NO está en Update: las aulas se comparten por facultad
# (así lo definimos desde el diseño del GA -- generar por facultad
# completa, no por carrera aislada, justo por esto). Reasignar un aula
# a otra facultad podría dejar corridas anteriores de horarios_asignados
# apuntando a una facultad que ya no coincide con la del aula.


class AulaCreate(BaseModel):
    facultad_id: int
    nombre: str
    capacidad: int
    tipo: str  # Ej: "Teorica", "Laboratorio", "Auditorio"


class AulaUpdate(BaseModel):
    nombre: str | None = None
    capacidad: int | None = None
    tipo: str | None = None
    activo: bool | None = None


router = crear_router_crud(
    tabla="aulas",
    prefijo="/aulas",
    tag="Aulas",
    modelo_create=AulaCreate,
    modelo_update=AulaUpdate,
)