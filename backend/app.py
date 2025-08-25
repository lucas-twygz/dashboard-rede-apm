from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import database
import analysis
import pandas as pd
import io

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
    if df.empty: return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    if start_date and end_date:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
    if ssid_filter:
        if ssid_filter == 'main_network': df = df[df['current_ssid'] == OPERATIONAL_SSID]
        elif ssid_filter == 'disconnected': df = df[df['current_ssid'] == 'disconnected']
        elif ssid_filter == 'other_networks': df = df[~df['current_ssid'].isin([OPERATIONAL_SSID, 'disconnected'])]
    if map_name and map_name in MAPS_CONFIG:
        bounds = MAPS_CONFIG[map_name]
        df = df[(df['latitude'].between(bounds['lat_bottom'], bounds['lat_top'])) & (df['longitude'].between(bounds['lon_left'], bounds['lon_right']))]
    return df.copy()

# --- ROTA PRINCIPAL ---
@app.route('/')
def index():
    return render_template('index.html')

# --- ROTAS DA API ---
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

# --- ENDPOINT DE EXPORTAÇÃO (ATUALIZADO) ---
@app.route('/api/export', methods=['GET'])
def export_excel_route():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)

    if not start_date or not end_date:
        return "Erro: As datas de início e fim são obrigatórias.", 400

    df = get_filtered_data(start_date=start_date, end_date=end_date)
    if df.empty:
        return "Nenhum dado encontrado para o período selecionado.", 404

    # --- NOVO: Separa Data e Hora ---
    df['Data'] = df['timestamp'].dt.strftime('%d/%m/%Y')
    df['Hora'] = df['timestamp'].dt.strftime('%H:%M:%S')

    # Dicionário de renomeação (não inclui mais o timestamp)
    column_mapping = {
        'tablet_android_id': 'Tablet (Android ID)',
        'signal_dbm': 'Sinal de Rede (dBm)',
        'current_ssid': 'Rede Wi-Fi Conectada',
        'packet_loss_percent': 'Perda de Pacotes (%)',
        'latitude': 'Latitude',
        'longitude': 'Longitude'
    }
    df_renamed = df.rename(columns=column_mapping)
    
    # Define a ordem final das colunas, incluindo as novas colunas de Data e Hora
    final_column_order = [
        'Tablet (Android ID)',
        'Data',
        'Hora',
        'Sinal de Rede (dBm)',
        'Rede Wi-Fi Conectada',
        'Perda de Pacotes (%)',
        'Latitude',
        'Longitude'
    ]
    df_final = df_renamed[final_column_order]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Usa a coluna 'Data' para agrupar e criar as abas
        for date_str, daily_data in df_final.groupby('Data'):
            # Converte a string da data para um objeto de data para formatar o nome da aba
            sheet_name_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            sheet_name = sheet_name_date.strftime('%d-%m-%Y')
            
            sorted_daily_data = daily_data.sort_values(by=['Rede Wi-Fi Conectada', 'Hora'])
            
            sorted_daily_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Auto-ajuste das colunas
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                header_length = len(str(worksheet[f'{column_letter}1'].value))
                max_length = header_length
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'Relatorio_WiFi_{start_date}_a_{end_date}.xlsx'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)