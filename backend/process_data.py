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
        full_df = pd.read_csv(CSV_PATH)
        total_lines_in_file = len(full_df)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{CSV_PATH}' não encontrado. Verifique o caminho.")
        return

    last_line = get_last_processed_line()
    new_data_df = full_df.iloc[last_line:].copy()
    
    if new_data_df.empty:
        print("Nenhuma nova linha encontrada. Processamento finalizado.")
        return

    print(f"Lendo {len(new_data_df)} novas linhas de dados.")
    
    try:
        # --- 1. Renomeia as colunas do CSV para o padrão do nosso banco ---
        column_mapping = {
            'sinal_avg_dbm': 'signal_dbm',
            'latencia_avg_ms': 'latency_ms'
            # As outras colunas já correspondem ou serão criadas
        }
        new_data_df.rename(columns=column_mapping, inplace=True)

        # --- 2. Combina as colunas 'data' e 'hora' para criar o 'timestamp' ---
        # Garante que as colunas de data/hora sejam tratadas como strings
        new_data_df['data'] = new_data_df['data'].astype(str)
        new_data_df['hora'] = new_data_df['hora'].astype(str)
        # O formato '%m-%d-%Y' corresponde a "08-25-2025"
        new_data_df['timestamp'] = pd.to_datetime(new_data_df['data'] + ' ' + new_data_df['hora'], format='%m-%d-%Y %H:%M:%S')

        # --- 3. Garante que os tipos de dados numéricos estão corretos ---
        numeric_cols = ['signal_dbm', 'packet_loss_percent', 'latency_ms', 'latitude', 'longitude']
        for col in numeric_cols:
            new_data_df[col] = pd.to_numeric(new_data_df[col])
            
        # Garante que o SSID seja uma string e preenche valores vazios
        new_data_df['current_ssid'].fillna('disconnected', inplace=True)
        new_data_df['current_ssid'] = new_data_df['current_ssid'].astype(str)

    except KeyError as e:
        print(f"Erro de schema: Coluna '{e}' ausente ou com nome incorreto no CSV. Verifique o cabeçalho.")
        return
    except Exception as e:
        print(f"Erro ao processar os dados: {e}")
        return

    # --- 4. Seleciona apenas as colunas que o banco de dados espera ---
    final_columns = [
        'tablet_android_id',
        'timestamp',
        'signal_dbm',
        'packet_loss_percent',
        'latitude',
        'longitude',
        'current_ssid',
        'latency_ms'
    ]
    df_to_save = new_data_df[final_columns]

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # --- ATENÇÃO: Descomente este bloco APENAS NA PRIMEIRA EXECUÇÃO ---
        # Este código adicionará a nova coluna 'latency_ms' à sua tabela.
        # try:
        #     conn.execute("ALTER TABLE raw_points ADD COLUMN latency_ms INTEGER;")
        #     print("Coluna 'latency_ms' adicionada com sucesso à tabela 'raw_points'.")
        # except sqlite3.OperationalError as e:
        #     if "duplicate column name" in str(e):
        #         print("Coluna 'latency_ms' já existe na tabela.")
        #     else:
        #         # Se for outro erro, exibe-o
        #         raise e
        
        df_to_save.to_sql('raw_points', conn, if_exists='append', index=False)
        print(f"{len(df_to_save)} linhas de dados processadas e salvas com sucesso no banco de dados.")

        save_last_processed_line(total_lines_in_file)
        print(f"Estado atualizado: {total_lines_in_file} linhas processadas no total.")
        
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    process_log_data()