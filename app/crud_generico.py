from typing import Type
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_connection
from auth import obtener_usuario_actual, ROL_ADMINISTRADOR


def _requerir_administrador(usuario: dict):
    if usuario["rol_id"] != ROL_ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="Solo un administrador puede realizar esta acción")


def crear_router_crud(
    tabla: str,
    prefijo: str,
    tag: str,
    modelo_create: Type[BaseModel],
    modelo_update: Type[BaseModel],
    tiene_activo: bool = True,
) -> APIRouter:
    """
    Genera un router con las operaciones CRUD estándar (listar, obtener,
    crear, actualizar, desactivar) para una tabla catálogo simple.

    IMPORTANTE sobre seguridad: 'tabla' y los nombres de columna que
    aparecen en 'modelo_create'/'modelo_update' NUNCA deben venir de
    datos del cliente -- siempre son valores fijos que tú defines en
    código al llamar a esta función (como se ve en facultades.py más
    abajo). Los VALORES sí vienen del cliente, pero siempre viajan
    parametrizados (%s), nunca concatenados directo al SQL. Por eso
    interpolar 'tabla' y los nombres de columna en el string es seguro
    aquí, aunque en general concatenar SQL no lo sea.

    - listar/obtener: cualquier usuario autenticado
    - crear/actualizar/desactivar: solo Administrador
    """
    router = APIRouter(prefix=prefijo, tags=[tag])

    @router.get("/")
    def listar(usuario: dict = Depends(obtener_usuario_actual)):
        conn = get_connection()
        cursor = conn.cursor()
        filtro = "WHERE activo = TRUE" if tiene_activo else ""
        cursor.execute(f"SELECT * FROM `{tabla}` {filtro} ORDER BY id")
        resultado = cursor.fetchall()
        conn.close()
        return resultado

    @router.get("/{item_id}")
    def obtener(item_id: int, usuario: dict = Depends(obtener_usuario_actual)):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `{tabla}` WHERE id = %s", (item_id,))
        resultado = cursor.fetchone()
        conn.close()
        if not resultado:
            raise HTTPException(status_code=404, detail=f"No encontrado en {tabla}")
        return resultado

    @router.post("/")
    def crear(datos: modelo_create, usuario: dict = Depends(obtener_usuario_actual)):
        _requerir_administrador(usuario)
        campos = datos.model_dump(exclude_unset=True)
        if not campos:
            raise HTTPException(status_code=400, detail="No se enviaron campos")

        columnas = ", ".join(f"`{c}`" for c in campos)
        placeholders = ", ".join(["%s"] * len(campos))

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"INSERT INTO `{tabla}` ({columnas}) VALUES ({placeholders})",
                tuple(campos.values()),
            )
            conn.commit()
            nuevo_id = cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return {"id": nuevo_id, "mensaje": "Creado correctamente"}

    @router.patch("/{item_id}")
    def actualizar(item_id: int, datos: modelo_update, usuario: dict = Depends(obtener_usuario_actual)):
        _requerir_administrador(usuario)
        campos = datos.model_dump(exclude_unset=True)
        if not campos:
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

        set_clause = ", ".join(f"`{c}` = %s" for c in campos)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE `{tabla}` SET {set_clause} WHERE id = %s",
                tuple(campos.values()) + (item_id,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return {"mensaje": "Actualizado correctamente"}

    if tiene_activo:
        @router.delete("/{item_id}")
        def desactivar(item_id: int, usuario: dict = Depends(obtener_usuario_actual)):
            _requerir_administrador(usuario)
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(f"UPDATE `{tabla}` SET activo = FALSE WHERE id = %s", (item_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            return {"mensaje": "Desactivado correctamente"}

    return router