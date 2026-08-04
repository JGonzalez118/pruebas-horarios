from pydantic import BaseModel
from crud_generico import crear_router_crud

# Esta tabla no tiene columna 'activo' en el schema, por eso
# tiene_activo=False -- no habrá endpoint DELETE (desactivar) para
# esta entidad. Si un tipo de contrato queda obsoleto, se recomienda
# simplemente dejar de usarlo en nuevos disponibilidad_x_profesor, en
# vez de eliminarlo (para no romper el historial de periodos pasados).


class ContratoCreate(BaseModel):
    nombre: str  # Ej: "Tiempo completo", "Medio tiempo", "Por horas"
    descripcion: str | None = None
    horas_max_semanales: int


class ContratoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    horas_max_semanales: int | None = None


router = crear_router_crud(
    tabla="contratos_profesores",
    prefijo="/contratos",
    tag="Contratos de Profesores",
    modelo_create=ContratoCreate,
    modelo_update=ContratoUpdate,
    tiene_activo=False,
)