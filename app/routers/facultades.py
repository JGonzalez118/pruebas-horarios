from pydantic import BaseModel
from crud_generico import crear_router_crud


class FacultadCreate(BaseModel):
    codigo_facultad: str
    nombre: str


class FacultadUpdate(BaseModel):
    codigo_facultad: str | None = None
    nombre: str | None = None
    activo: bool | None = None


router = crear_router_crud(
    tabla="facultades",
    prefijo="/facultades",
    tag="Facultades",
    modelo_create=FacultadCreate,
    modelo_update=FacultadUpdate,
)