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

# --- FUNÇÃO HELPER CENTRALIZADA (ATUALIZADA) ---
def get_filtered_data(map_name=None, start_date=None, end_date=None):
    """
    Busca todos os pontos e filtra por mapa e/ou intervalo de datas.
    """
    df = database.get_all_raw_points()
    if df.empty:
        return df

    # Converte timestamp para datetime para permitir a filtragem
    # O errors='coerce' transforma datas inválidas em NaT (Not a Time)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True) # Remove linhas com datas inválidas

    # --- NOVO: Filtro por data ---
    if start_date and end_date:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59) # Inclui o dia todo
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]

    # Filtro por mapa (geográfico)
    if map_name and map_name in MAPS_CONFIG:
        bounds = MAPS_CONFIG[map_name]
        df = df[
            (df['latitude'].between(bounds['lat_bottom'], bounds['lat_top'])) &
            (df['longitude'].between(bounds['lon_left'], bounds['lon_right']))
        ]
    
    return df.copy()

# --- ROTAS DA API (ATUALIZADAS) ---
@app.route('/api/map_data', methods=['GET'])
def map_data_route():
    map_name = request.args.get('map', None)
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    df_filtered = get_filtered_data(map_name, start_date, end_date)
    zones_data = analysis.generate_map_data(df_filtered)
    return jsonify(zones_data)

@app.route('/api/critical_points', methods=['GET'])
def critical_points_route():
    map_name = request.args.get('map', None)
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)

    df_filtered = get_filtered_data(map_name, start_date, end_date)
    chart_data = analysis.get_top_problem_locations(df_filtered)
    return jsonify(chart_data)

# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)