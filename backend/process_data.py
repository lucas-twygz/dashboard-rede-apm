import pandas as pd
import sqlite3
import os

# --- CONFIGURAÇÃO ---
DB_PATH = 'db/dashboard.db'
# Certifique-se de que este caminho está correto para a sua máquina
CSV_PATH = r'C:\APPS\Check Signal\data\raw_data.csv' 
# <<< LINHA CORRIGIDA >>>
STATE_FILE_PATH = 'db/.last_processed_line'

def get_last_processed_line():
    """Lê o número da última linha processada do arquivo de estado."""
    try:
        with open(STATE_FILE_PATH, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_last_processed_line(line_count):
    """Salva o número total de linhas processadas no arquivo de estado."""
    with open(STATE_FILE_PATH, 'w') as f:
        f.write(str(line_count))

def process_log_data():
    print("Iniciando ETL: Lendo novos dados brutos...")
    
    try:
        full_df = pd.read_csv(CSV_PATH)
        total_lines_in_file = len(full_df)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{CSV_PATH}' não encontrado. Verifique o caminho.")
        return

    last_line = get_last_processed_line()
    df = full_df.iloc[last_line:].copy()
    
    if df.empty:
        print("Nenhuma nova linha encontrada. Processamento finalizado.")
        return

    print(f"Lendo {len(df)} novas linhas de dados.")
    
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['latitude'] = pd.to_numeric(df['latitude'])
        df['longitude'] = pd.to_numeric(df['longitude'])
        
    except KeyError as e:
        print(f"Erro de schema: Coluna '{e}' ausente no CSV.")
        return
    except Exception as e:
        print(f"Erro ao processar os dados: {e}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('raw_points', conn, if_exists='append', index=False)
        print("Dados processados e salvos com sucesso no banco de dados.")

        save_last_processed_line(total_lines_in_file)
        print(f"Estado atualizado: {total_lines_in_file} linhas processadas no total.")
        
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    process_log_data()