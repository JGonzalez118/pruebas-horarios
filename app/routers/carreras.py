from pydantic import BaseModel
from crud_generico import crear_router_crud

# facultad_id NO está en Update a propósito: cambiar la facultad de una
# carrera después de creada rompería los supuestos que ya validamos
# (aulas compartidas por facultad, profesores por facultad). Si en el
# futuro necesitas reasignarla, se hace con un endpoint dedicado con
# confirmación explícita, igual que grupos.carrera_id más abajo.


class CarreraCreate(BaseModel):
    facultad_id: int
    codigo_carrera: str
    nombre: str


class CarreraUpdate(BaseModel):
    codigo_carrera: str | None = None
    nombre: str | None = None
    activo: bool | None = None


router = crear_router_crud(
    tabla="carreras",
    prefijo="/carreras",
    tag="Carreras",
    modelo_create=CarreraCreate,
    modelo_update=CarreraUpdate,
)