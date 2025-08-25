# Importa render_template para servir o HTML
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import database
import analysis
import pandas as pd

# Define o caminho para as pastas de templates e arquivos estáticos
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# --- CONFIGURAÇÕES GLOBAIS ---
BUFFER_GPS = 0.005
TMUT_CENTER_LAT = -3.525506
TMUT_CENTER_LON = -38.797690
OPERATIONAL_SSID = "2G_6qmzayp"

MAPS_CONFIG = {
    'patio': { 'lat_top': -3.543, 'lat_bottom': -3.556, 'lon_left': -38.822, 'lon_right': -38.802 },
    'tmut': { 'lat_top': TMUT_CENTER_LAT + BUFFER_GPS, 'lat_bottom': TMUT_CENTER_LAT - BUFFER_GPS, 'lon_left': TMUT_CENTER_LON - BUFFER_GPS, 'lon_right': TMUT_CENTER_LON + BUFFER_GPS }
}

# --- FUNÇÃO HELPER ---
def get_filtered_data(map_name=None, start_date=None, end_date=None, ssid_filter=None):
    df = database.get_all_raw_points()
    if df.empty:
        return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    if start_date and end_date:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
    if ssid_filter:
        if ssid_filter == 'main_network':
            df = df[df['current_ssid'] == OPERATIONAL_SSID]
        elif ssid_filter == 'disconnected':
            df = df[df['current_ssid'] == 'disconnected']
        elif ssid_filter == 'other_networks':
            df = df[~df['current_ssid'].isin([OPERATIONAL_SSID, 'disconnected'])]
    if map_name and map_name in MAPS_CONFIG:
        bounds = MAPS_CONFIG[map_name]
        df = df[
            (df['latitude'].between(bounds['lat_bottom'], bounds['lat_top'])) &
            (df['longitude'].between(bounds['lon_left'], bounds['lon_right']))
        ]
    return df.copy()

# --- NOVA ROTA PARA SERVIR A APLICAÇÃO ---
@app.route('/')
def index():
    """Serve o arquivo principal da aplicação (index.html)."""
    return render_template('index.html')

# --- ROTAS DA API (Permanecem as mesmas, mas agora com o prefixo /api/) ---
@app.route('/api/map_data', methods=['GET'])
def map_data_route():
    map_name = request.args.get('map', 'patio')
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    ssid_filter = request.args.get('ssid_filter', 'main_network')
    df_filtered = get_filtered_data(map_name, start_date, end_date, ssid_filter)
    zones_data = analysis.generate_map_data(df_filtered)
    return jsonify(zones_data)

@app.route('/api/critical_points', methods=['GET'])
def critical_points_route():
    map_name = request.args.get('map', 'patio')
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    ssid_filter = request.args.get('ssid_filter', 'main_network')
    df_filtered = get_filtered_data(map_name, start_date, end_date, ssid_filter)
    chart_data = analysis.get_top_problem_locations(df_filtered)
    return jsonify(chart_data)

# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Usar host='0.0.0.0' torna o servidor acessível na sua rede local
    app.run(host='0.0.0.0', debug=True)