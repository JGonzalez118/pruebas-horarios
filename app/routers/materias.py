from pydantic import BaseModel
from crud_generico import crear_router_crud

# departamento_id NO está en Update: cambiarlo después de creada rompe
# la lógica de /profesores/elegibles-para-materia, que filtra por
# coincidencia de departamento entre profesor y materia.


class MateriaCreate(BaseModel):
    departamento_id: int
    codigo_materia: str
    nombre: str
    creditos: int = 0
    creditos_minimos_docente: int = 0


class MateriaUpdate(BaseModel):
    codigo_materia: str | None = None
    nombre: str | None = None
    creditos: int | None = None
    creditos_minimos_docente: int | None = None
    activo: bool | None = None


router = crear_router_crud(
    tabla="materias",
    prefijo="/materias",
    tag="Materias",
    modelo_create=MateriaCreate,
    modelo_update=MateriaUpdate,
)