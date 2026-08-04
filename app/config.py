import os
from dotenv import load_dotenv

load_dotenv()


def _leer_int(nombre_variable: str, valor_default: int) -> int:
    """
    Convierte la variable de entorno a int de forma defensiva. Si el
    .env trae espacios, saltos de línea invisibles, o el valor viene
    vacío, esto evita que pymysql falle con un error poco claro más
    adelante (como 'port should be of type int').
    """
    valor = os.getenv(nombre_variable)
    if valor is None or valor.strip() == "":
        return valor_default
    try:
        return int(valor.strip())
    except ValueError:
        raise ValueError(
            f"La variable {nombre_variable}='{valor}' en tu .env no es un "
            f"número válido. Revisa que no tenga comillas, espacios ni comentarios."
        )


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = _leer_int("DB_PORT", 3306)
    DB_NAME: str = os.getenv("DB_NAME", "sistema_horarios_ga")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = _leer_int("JWT_EXPIRATION_MINUTES", 480)


settings = Settings()