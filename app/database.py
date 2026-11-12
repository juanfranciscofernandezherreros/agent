import sqlite3
from .config import DB_PATH

def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, git_url TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL, source_path TEXT,
            analysis_json TEXT, reconstruction_json TEXT, last_error TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS equivalence_runs (
            id TEXT PRIMARY KEY, project_id TEXT, created_at TEXT NOT NULL,
            result_json TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS generation_runs (
            id TEXT PRIMARY KEY, project_id TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL, result_json TEXT, error TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS repair_runs (
            id TEXT PRIMARY KEY, generation_id TEXT NOT NULL, equivalence_run_id TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL, result_json TEXT, error TEXT)""")
