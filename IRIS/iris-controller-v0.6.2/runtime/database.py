from pathlib import Path
import sqlite3
DB_PATH=Path(__file__).parent/'data'/'iris.db'
def get_connection():
 DB_PATH.parent.mkdir(parents=True,exist_ok=True); conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; return conn
def init_db():
 with get_connection() as conn: conn.executescript('''CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,status TEXT NOT NULL,topic TEXT NOT NULL,fact TEXT NOT NULL,source TEXT NOT NULL,verification_state TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS work_units(id TEXT PRIMARY KEY,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'CREATED',current_step INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS step_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,step INTEGER NOT NULL,attempt INTEGER NOT NULL,status TEXT NOT NULL,expected TEXT,actual TEXT,note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS errors(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,step INTEGER,attempt INTEGER,error_type TEXT NOT NULL,message TEXT NOT NULL,expected TEXT,actual TEXT,root_cause TEXT,impact TEXT,correction TEXT,verification TEXT,prevention_rule TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS checkpoints(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,step INTEGER NOT NULL,state TEXT NOT NULL,snapshot TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS verifications(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,expected TEXT NOT NULL,actual TEXT NOT NULL,status TEXT NOT NULL,note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,work_id TEXT NOT NULL,action TEXT NOT NULL,details TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);''')
def one(sql,args=()):
 with get_connection() as conn:
  r=conn.execute(sql,args).fetchone(); return dict(r) if r else None
def many(sql,args=()):
 with get_connection() as conn:return [dict(r) for r in conn.execute(sql,args).fetchall()]
