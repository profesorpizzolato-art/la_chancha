import os
import random
import sqlite3
from datetime import datetime

# Obtenemos la ruta absoluta del directorio donde se encuentra este archivo database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "la_chancha.db")

def conn():
    # Creamos la carpeta 'data' usando la ruta absoluta si no existe
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    
    # timeout evita bloqueos concurrentes de SQLite en Streamlit Cloud
    return sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
