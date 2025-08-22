from flask import Flask, jsonify, request
from flask_cors import CORS
import database
import analysis
import pandas as pd # É uma boa prática garantir que pandas está importado

app = Flask(__name__)
CORS(app)

# --- CONFIGURAÇÕES GLOBAIS ---

# Define um "buffer" para criar a caixa ao redor do ponto central.
# 0.005 graus é aproximadamente 550 metros.
BUFFER_GPS = 0.005

# Coordenada central correta para o TMUT que você forneceu
TMUT_CENTER_LAT = -3.525506
TMUT_CENTER_LON = -38.797690

# Dicionário com as "caixas" geográficas para cada mapa
MAPS_CONFIG = {
    'patio': {
        # Caixa ajustada para uma área provável do pátio.
        # Estes valores você pode ajustar olhando no Google Maps.
        'lat_top': -3.543,
        'lat_bottom': -3.556,
        'lon_left': -38.822,
        'lon_right': -38.802  # Corrigido o erro de digitação
    },
    'tmut': {
        # Caixa calculada a partir do ponto central correto
        'lat_top': TMUT_CENTER_LAT + BUFFER_GPS,
        'lat_bottom': TMUT_CENTER_LAT - BUFFER_GPS,
        'lon_left': TMUT_CENTER_LON - BUFFER_GPS,
        'lon_right': TMUT_CENTER_LON + BUFFER_GPS
    }
}

# --- FUNÇÃO HELPER CENTRALIZADA ---

def get_filtered_data_by_map(map_name):
    """
    Busca todos os pontos do banco de dados e filtra por um mapa específico
    se um nome de mapa válido for fornecido.
    
    Args:
        map_name (str or None): O nome do mapa para filtrar (ex: 'patio', 'tmut').
    
    Returns:
        pandas.DataFrame: Um DataFrame contendo os pontos filtrados.
    """
    # Busca todos os dados brutos do banco
    df = database.get_all_raw_points()

    # Se um nome de mapa foi passado e ele existe na nossa configuração...
    if map_name and map_name in MAPS_CONFIG:
        bounds = MAPS_CONFIG[map_name]
        # Filtra o DataFrame para conter apenas pontos dentro dos limites geográficos
        df_filtered = df[
            (df['latitude'].between(bounds['lat_bottom'], bounds['lat_top'])) &
            (df['longitude'].between(bounds['lon_left'], bounds['lon_right']))
        ]
        # Usar .copy() é uma boa prática para evitar "SettingWithCopyWarning" do Pandas
        return df_filtered.copy()
    
    # Se nenhum mapa for especificado, retorna todos os dados
    return df

# --- ROTAS DA API ---

@app.route('/api/map_data', methods=['GET'])
def map_data_route():
    """
    Endpoint que retorna os dados das zonas (clusters) para o mapa.
    Agora respeita o filtro de mapa passado via query string.
    Ex: /api/map_data?map=tmut
    """
    map_name = request.args.get('map', None)
    df_filtered = get_filtered_data_by_map(map_name)
    
    # A análise de zonas agora é feita apenas com os dados filtrados
    zones_data = analysis.generate_map_data(df_filtered)
    return jsonify(zones_data)

@app.route('/api/critical_points', methods=['GET'])
def critical_points_route():
    """
    Endpoint que retorna os dados para o gráfico Top 10.
    Respeita o filtro de mapa passado via query string.
    Ex: /api/critical_points?map=tmut
    """
    map_name = request.args.get('map', None)
    df_filtered = get_filtered_data_by_map(map_name)

    # A análise do Top 10 agora é feita apenas com os dados filtrados
    chart_data = analysis.get_top_critical_points(df_filtered)
    return jsonify(chart_data)

# --- INICIALIZAÇÃO DO SERVIDOR ---

if __name__ == '__main__':
    # O debug=True é ótimo para desenvolvimento, pois reinicia o servidor
    # automaticamente a cada alteração no código.
    app.run(debug=True)