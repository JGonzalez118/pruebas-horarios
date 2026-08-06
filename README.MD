
# Generación de Horarios | pruebas [usa python 3.12]

## Base de datos
- Crea la base de datos con el script horariosv1.sql
- Llena la base de datos con el script seed_sistema_horarios.sql 

## Entorno
Crea el entorno de python 
```
python -m venv .venv
```
Activalo (powershell)
```
.venv\Scripts\Activate.ps1
```
o con cmd
```
.venv\Scripts\activate.bat
```

Instala los paquetes
```
pip install -r requirements.txt
```

## Corre la API
muevete a la carpeta app/ y pon:
```
uvicorn main:app --reload
```

abres http://127.0.0.1:8000/docs y ahí estan los endpoints para probar

# IMPORTANTE 
si tienes problemas con la conexión de la base de datos entonces en la raíz del programa haz un archivo .env con esto
```
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="sistema_horarios_ga"
DB_USER="root"
DB_PASSWORD="tu contraseña si la tienes puesta a tu mariadb"
```
ADEMAS DEBES PONER ESTO TAMBIÉN:
```
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=480
```

La secret key la generas con esto, puedes ir a un interpreter de python en linea y correr esto y copias el resultado
```
import secrets; 

print(secrets.token_hex(32))
```
