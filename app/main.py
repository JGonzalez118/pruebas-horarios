from fastapi import FastAPI
from routers import (restricciones, generacion, resultados, profesores, auth, usuarios, facultades, 
                    carreras, materias, grupos, aulas, contratos, periodos_academicos, carga_academica)

app = FastAPI(
    title="API de Pruebas — Algoritmo Genético para Horarios",
    description="Laboratorio aislado, conecta a sistema_horarios_ga (no toca la BD real).",
)

app.include_router(restricciones.router)
app.include_router(generacion.router)
app.include_router(resultados.router)
app.include_router(profesores.router)
app.include_router(usuarios.router)
app.include_router(auth.router)
app.include_router(facultades.router)
app.include_router(carreras.router)
app.include_router(materias.router)
app.include_router(grupos.router)
app.include_router(aulas.router)
app.include_router(contratos.router)
app.include_router(periodos_academicos.router)
app.include_router(carga_academica.router)

@app.get("/")
def raiz():
    return {"status": "ok", "mensaje": "API de pruebas del GA activa"}
