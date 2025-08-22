from flask import Flask, jsonify, request
from flask_cors import CORS
import database
import analysis
import pandas as pd

app = Flask(__name__)
CORS(app)

# --- CONFIGURAÇÕES GLOBAIS ---

BUFFER_GPS = 0.005
TMUT_CENTER_LAT = -3.525506
TMUT_CENTER_LON = -38.797690

MAPS_CONFIG = {
    'patio': {
        'lat_top': -3.543,
        'lat_bottom': -3.556,
        'lon_left': -38.822,
        'lon_right': -38.802
    },
    'tmut': {
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
    """
    df = database.get_all_raw_points()
    if map_name and map_name in MAPS_CONFIG:
        bounds = MAPS_CONFIG[map_name]
        df_filtered = df[
            (df['latitude'].between(bounds['lat_bottom'], bounds['lat_top'])) &
            (df['longitude'].between(bounds['lon_left'], bounds['lon_right']))
        ]
        return df_filtered.copy()
    return df

# --- ROTAS DA API ---

@app.route('/api/map_data', methods=['GET'])
def map_data_route():
    """
    Endpoint que retorna os dados das zonas (clusters) para o mapa.
    Agora respeita o filtro de mapa passado via query string.
    """
    map_name = request.args.get('map', None)
    df_filtered = get_filtered_data_by_map(map_name)
    zones_data = analysis.generate_map_data(df_filtered)
    return jsonify(zones_data)

@app.route('/api/critical_points', methods=['GET'])
def critical_points_route():
    """
    Endpoint que retorna os dados para o gráfico Top 10.
    Respeita o filtro de mapa passado via query string.
    """
    map_name = request.args.get('map', None)
    df_filtered = get_filtered_data_by_map(map_name)

    # A análise do Top 10 agora é feita apenas com os dados filtrados
    # <<< LINHA CORRIGIDA >>>
    chart_data = analysis.get_top_problem_locations(df_filtered)
    return jsonify(chart_data)

# --- INICIALIZAÇÃO DO SERVIDOR ---

if __name__ == '__main__':
    app.run(debug=True)