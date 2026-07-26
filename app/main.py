from fastapi import FastAPI
from routers import restricciones, generacion, resultados, profesores

app = FastAPI(
    title="API de Pruebas — Algoritmo Genético para Horarios",
    description="Laboratorio aislado, conecta a sistema_horarios_ga (no toca la BD real).",
)

app.include_router(restricciones.router)
app.include_router(generacion.router)
app.include_router(resultados.router)
app.include_router(profesores.router)


@app.get("/")
def raiz():
    return {"status": "ok", "mensaje": "API de pruebas del GA activa"}
