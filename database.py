import os
import random
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "la_chancha.db")

def conn():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)

def init_db():
    with conn() as c:
        cur = c.cursor()
        # Tabla de Sorteos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                prize_percent REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                winning_ticket TEXT
            )
        """)
        # Tabla de Pagos / Ordenes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_id INTEGER NOT NULL,
                payment_id TEXT UNIQUE,
                payer_name TEXT NOT NULL,
                payer_email TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TEXT NOT NULL
            )
        """)
        # Tabla de Participantes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_id INTEGER NOT NULL,
                payment_id TEXT,
                ticket TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        c.commit()

def create_draw(name, price, start, end, prize_percent):
    start_str = start.isoformat() if isinstance(start, datetime) else start
    end_str = end.isoformat() if isinstance(end, datetime) else end

    with conn() as c:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO draws(name, price, start, end, prize_percent) VALUES(?, ?, ?, ?, ?)",
            (name, price, start_str, end_str, prize_percent)
        )
        c.commit()

def get_draw(draw_id=None):
    with conn() as c:
        cur = c.cursor()
        if draw_id:
            cur.execute("SELECT * FROM draws WHERE id=?", (draw_id,))
        else:
            cur.execute("SELECT * FROM draws ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
    
    if not row:
        return None
    keys = ["id", "name", "price", "start", "end", "prize_percent", "status", "winning_ticket"]
    return dict(zip(keys, row))

def close_draw(draw_id: int) -> bool:
    """Cierra manualmente un sorteo de forma segura."""
    try:
        with conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE draws SET status = 'CLOSED' WHERE id = ?", (draw_id,))
            c.commit()
            return True
    except Exception as e:
        print(f"Error al cerrar el sorteo {draw_id}: {e}")
        return False

def get_participants(draw_id):
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            "SELECT ticket, name, created_at FROM participants WHERE draw_id=? ORDER BY id",
            (draw_id,)
        )
        rows = cur.fetchall()
    return [{"ticket": r[0], "name": r[1], "created_at": r[2]} for r in rows]

def register_successful_payment(draw_id, payment_id, name, email, quantity):
    """
    Registra el pago de forma idempotente: si el payment_id ya fue procesado,
    retorna los tickets existentes en lugar de duplicarlos.
    """
    with conn() as c:
        cur = c.cursor()
        
        # 1. Validar si ya se emitieron tickets para este payment_id
        if payment_id:
            cur.execute("SELECT ticket FROM participants WHERE payment_id=?", (str(payment_id),))
            existing = cur.fetchall()
            if existing:
                return [r[0] for r in existing]

        # 2. Si es una transacción nueva, emitir tickets
        tickets_generados = []
        for _ in range(quantity):
            inserted = False
            for _ in range(5): # Reintentos si hay colisión de ticket aleatorio
                ticket = f"LC-{random.randint(100000, 999999)}-{random.randint(10, 99)}"
                try:
                    cur.execute(
                        "INSERT INTO participants(draw_id, payment_id, ticket, name, email, created_at) VALUES(?, ?, ?, ?, ?, ?)",
                        (draw_id, str(payment_id), ticket, name, email, datetime.now().isoformat())
                    )
                    tickets_generados.append(ticket)
                    inserted = True
                    break
                except sqlite3.IntegrityError:
                    continue
            if not inserted:
                print(f"Warning: No se pudo generar ticket único tras varios intentos.")
                
        c.commit()
    return tickets_generados

def draw_winner(draw_id):
    with conn() as c:
        cur = c.cursor()
        cur.execute("SELECT ticket, name FROM participants WHERE draw_id=?", (draw_id,))
        rows = cur.fetchall()
        if not rows:
            return None
        
        winner = random.SystemRandom().choice(rows)
        cur.execute(
            "UPDATE draws SET status='CLOSED', winning_ticket=? WHERE id=?",
            (winner[0], draw_id)
        )
        c.commit()
    return {"ticket": winner[0], "name": winner[1]}
