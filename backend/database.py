import sqlite3
import pandas as pd

DB_PATH = 'db/dashboard.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_raw_points():
    """Busca todos os pontos brutos da tabela raw_points."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM raw_points", conn)
    conn.close()
    return df