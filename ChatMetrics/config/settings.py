# config/settings.py
import os
import sys

# Configuración General
APP_NAME = "ChatMetrics"
APP_VERSION = "1.0.0"

# Columnas esperadas en el Excel de entrada
# Estas pueden ser editadas por el usuario si cambian los nombres en los reportes originales
COL_FECHA = "Fecha del mensaje"
COL_CAMPAÑA = "Nombre de campaña"

# Clasificación de Campañas según sub-cadenas
# Diccionario donde la llave es el nombre a mostrar en el reporte y el valor es una lista de palabras clave para buscar
POSTGRADO_KEYWORDS = {
    "PEE": ["PEE"],
    "Maestría (M.)": ["M.", "Maestrías", "Maestrias", "Maestria"],
    "Quicklearning": ["Quicklearning", "Quick Learning"],
    "Diplomas": ["Diplomas"],
    "PADE": ["PADE"],
    "CIE": ["CIE"],
    "MBA": ["MBA"],
    "PAE": ["PAE"]
}

PREGRADO_KEYWORDS = {
    "Universidad ESAN – Pregrado (5to año)": ["Universidad ESAN - Pregrado (5to año)", "Universidad ESAN – Pregrado (5to año)"],
    "Universidad Esan Pregrado (Egresado)": ["Universidad Esan Pregrado (Egresado)"],
    "Extended Learning": ["Extended Learning"],
    "Universidad ESAN – DPA": ["Universidad ESAN - DPA", "Universidad ESAN – DPA"]
}

# Columnas que representan cada paso del embudo
# En el Excel estas columnas contienen valores como (Exitosa | Pendiente | Fallida | N/A)
COLUMNAS_EMBUDO = [
    "Salida",
    "Envío",
    "Entrega",
    "Lectura",
    "Respuesta"
]

# Rutas predeterminadas (compatible con PyInstaller)
if hasattr(sys, '_MEIPASS'):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.join(_BASE_DIR, "logs")
EXPORTS_DIR = os.path.join(_BASE_DIR, "exports")

# Crear directorios si no existen
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
