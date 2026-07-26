import pymysql
import pymysql.cursors

from config import settings


def get_connection():
    """
    Abre una nueva conexión por request. Para una API de pruebas esto
    es suficiente; en producción se recomendaría un pool de conexiones
    (mariadb.ConnectionPool), pero eso lo dejamos para la fase real
    del proyecto, no para este laboratorio.
    """
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
