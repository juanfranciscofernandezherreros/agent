# Corpus: módulo homónimo seguro (consulta parametrizada).
import sqlite3


def find_user(name):
    conn = sqlite3.connect("users.db")
    return conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
