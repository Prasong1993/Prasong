"""IRIS database layer — SQLite persistence with env-overridable path."""
import os
import sqlite3
from pathlib import Path
_DEFAULT_DB_PATH=Path(__file__).parent/"data"/"iris.db"
DB_PATH=Path(os.environ.get("IRIS_DB_PATH")) if os.environ.get("IRIS_DB_PATH") else _DEFAULT_DB_PATH
def get_db_path():
    env=os.environ.get("IRIS_DB_PATH")
    return Path(env) if env else DB_PATH
def set_db_path(path):
    global DB_PATH
    DB_PATH=Path(path); os.environ["IRIS_DB_PATH"]=str(DB_PATH)
def get_connection():
    path=get_db_path(); path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path); conn.row_factory=sqlite3.Row; return conn
_SCHEMA="""CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,status TEXT NOT NULL,topic TEXT NOT NULL,fact TEXT NOT NULL,source TEXT NOT NULL,verification_state TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS work_units(id TEXT PRIMARY KEY,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'CREATED',current_step INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS step_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,step INTEGER NOT NULL,attempt INTEGER NOT NULL,status TEXT NOT NULL,expected TEXT,actual TEXT,note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS errors(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,step INTEGER,attempt INTEGER,error_type TEXT NOT NULL,message TEXT NOT NULL,expected TEXT,actual TEXT,root_cause TEXT,impact TEXT,correction TEXT,verification TEXT,prevention_rule TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS checkpoints(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,step INTEGER NOT NULL,state TEXT NOT NULL,snapshot TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS verifications(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,expected TEXT NOT NULL,actual TEXT NOT NULL,status TEXT NOT NULL,note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,action TEXT NOT NULL,details TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"""
def init_db():
    with get_connection() as c:c.executescript(_SCHEMA)
def one(sql,args=()):
    with get_connection() as c:
        r=c.execute(sql,args).fetchone(); return dict(r) if r else None
def many(sql,args=()):
    with get_connection() as c:return [dict(r) for r in c.execute(sql,args).fetchall()]
