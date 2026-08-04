from dbutils.pooled_db import PooledDB
import pymysql
import pymysql.cursors

from config import settings

#* objeto 'pool' para no saturar al servidor con traficos altos
pool = PooledDB(
    creator=pymysql,
    maxconnections=10,  # * CANTIDAD DE CONEXIONES SIMULTANEAS
    mincached=2,
    maxcached=5,
    blocking=True,      #* si se agotan las conexiones disponibles el siguiente request espera a que se libere una
    ping=1,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
)


def get_connection():
    return pool.connection()
