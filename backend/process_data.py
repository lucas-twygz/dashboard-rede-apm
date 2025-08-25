import pandas as pd
import sqlite3
import os

# --- CONFIGURAÇÃO ---
DB_PATH = 'db/dashboard.db'
CSV_PATH = r'C:\APPS\Check Signal\data\raw_data.csv' 
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
        # Garante que a coluna current_ssid seja lida como string
        full_df = pd.read_csv(CSV_PATH, dtype={'current_ssid': str})
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
        # --- NOVO: Tratamento da coluna current_ssid ---
        if 'current_ssid' not in df.columns:
            print("Erro de schema: Coluna 'current_ssid' ausente no CSV.")
            return
            
        # Preenche valores nulos ou vazios (NaN) em 'current_ssid' com 'disconnected'
        df['current_ssid'].fillna('disconnected', inplace=True)
        df['current_ssid'] = df['current_ssid'].astype(str)

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
        
        # --- ATENÇÃO: Primeira execução para adicionar a coluna ---
        # Descomente o bloco abaixo APENAS NA PRIMEIRA VEZ que executar este script
        # para adicionar a nova coluna na tabela existente sem precisar recriar o banco.
        # try:
        #     conn.execute("ALTER TABLE raw_points ADD COLUMN current_ssid TEXT;")
        #     print("Coluna 'current_ssid' adicionada à tabela 'raw_points'.")
        # except sqlite3.OperationalError as e:
        #     if "duplicate column name" in str(e):
        #         print("Coluna 'current_ssid' já existe.")
        #     else:
        #         raise e
        
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