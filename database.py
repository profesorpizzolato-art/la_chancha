import sqlite3
from datetime import datetime
import random

DB = "data/la_chancha.db"

def conn():
    return sqlite3.connect(DB)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS draws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        start TEXT NOT NULL,
        end TEXT NOT NULL,
        prize_percent REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        winner_ticket TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draw_id INTEGER NOT NULL,
        ticket TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    c.commit()
    c.close()

def create_draw(name, price, start, end, prize_percent):
    c = conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO draws(name,price,start,end,prize_percent) VALUES(?,?,?,?,?)",
        (name, price, start.isoformat(), end.isoformat(), prize_percent)
    )
    c.commit()
    c.close()

def get_draw(draw_id=None):
    c = conn()
    cur = c.cursor()
    if draw_id:
        cur.execute("SELECT * FROM draws WHERE id=?", (draw_id,))
    else:
        cur.execute("SELECT * FROM draws ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    c.close()
    if not row:
        return None
    keys = ["id","name","price","start","end","prize_percent","status","winner_ticket"]
    return dict(zip(keys,row))

def get_participants(draw_id):
    c = conn()
    cur = c.cursor()
    cur.execute(
        "SELECT ticket,name,created_at FROM participants WHERE draw_id=? ORDER BY id",
        (draw_id,)
    )
    rows = cur.fetchall()
    c.close()
    return [{"ticket":r[0],"name":r[1],"created_at":r[2]} for r in rows]

def add_demo_participants(draw_id, quantity, price):
    c = conn()
    cur = c.cursor()
    for _ in range(quantity):
        ticket = f"LC-{random.randint(100000,999999)}-{random.randint(10,99)}"
        try:
            cur.execute(
                "INSERT INTO participants(draw_id,ticket,name,created_at) VALUES(?,?,?,?)",
                (draw_id,ticket,"Participante Demo",datetime.now().isoformat())
            )
        except sqlite3.IntegrityError:
            pass
    c.commit()
    c.close()

def draw_winner(draw_id):
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT ticket,name FROM participants WHERE draw_id=?", (draw_id,))
    rows = cur.fetchall()
    if not rows:
        c.close()
        return None
    winner = random.SystemRandom().choice(rows)
    cur.execute(
        "UPDATE draws SET status='CLOSED', winner_ticket=? WHERE id=?",
        (winner[0], draw_id)
    )
    c.commit()
    c.close()
    return {"ticket":winner[0], "name":winner[1]}
