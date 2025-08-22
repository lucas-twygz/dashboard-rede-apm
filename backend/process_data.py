import pandas as pd
import sqlite3
import os

DB_FOLDER = 'db'
CSV_FILE_PATH = r'C:\APPS\Check Signal\data\raw_data.csv'
DB_FILE_PATH = os.path.join(DB_FOLDER, 'dashboard.db')
CONTROL_FILE_PATH = os.path.join(DB_FOLDER, 'last_processed.txt')

def setup_environment():
    if not os.path.exists(DB_FOLDER): os.makedirs(DB_FOLDER)

def initialize_database():
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS raw_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, tablet_android_id TEXT,
        signal_dbm REAL, latency_ms REAL, packet_loss_percent REAL,
        latitude REAL, longitude REAL
    )
    ''')
    conn.commit()
    conn.close()

def get_last_processed_line():
    if not os.path.exists(CONTROL_FILE_PATH): return 0
    with open(CONTROL_FILE_PATH, 'r') as f:
        try: return int(f.read().strip())
        except (ValueError, IndexError): return 0

def update_last_processed_line(line_count):
    with open(CONTROL_FILE_PATH, 'w') as f: f.write(str(line_count))

def process_log_data():
    print("Iniciando ETL: Lendo novos dados brutos...")
    last_line = get_last_processed_line()
    try:
        df = pd.read_csv(CSV_FILE_PATH, skiprows=range(1, last_line + 1))
        if df.empty: print("Nenhum dado novo para processar."); return
        new_total_lines = last_line + len(df)
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}"); return

    print(f"Lendo {len(df)} novas linhas de dados.")
    df['timestamp'] = pd.to_datetime(df['data'] + ' ' + df['hora'])
    df_to_save = df[['timestamp', 'tablet_android_id', 'sinal_avg_dbm', 'latencia_avg_ms', 'packet_loss_percent', 'latitude', 'longitude']].copy()
    df_to_save.rename(columns={'sinal_avg_dbm': 'signal_dbm', 'latencia_avg_ms': 'latency_ms'}, inplace=True)
    conn = sqlite3.connect(DB_FILE_PATH)
    df_to_save.to_sql('raw_points', conn, if_exists='append', index=False)
    conn.close()
    update_last_processed_line(new_total_lines)
    print(f"Novos dados salvos no banco. Total de linhas processadas: {new_total_lines}.")

if __name__ == '__main__':
    setup_environment()
    initialize_database()
    process_log_data()