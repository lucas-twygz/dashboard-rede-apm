from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import database
import analysis
import pandas as pd
import io
from collections import Counter
from waitress import serve
import random
import time

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# --- CONFIGURAÇÕES GLOBAIS ---
BUFFER_GPS = 0.005
TMUT_CENTER_LAT = -3.525506
TMUT_CENTER_LON = -38.797690
OPERATIONAL_SSID = "2G_6qmzayp"
MAPS_CONFIG = {
    'patio': {'lat_top': -3.543, 'lat_bottom': -3.556, 'lon_left': -38.822, 'lon_right': -38.802},
    'tmut': {'lat_top': TMUT_CENTER_LAT + BUFFER_GPS, 'lat_bottom': TMUT_CENTER_LAT - BUFFER_GPS,
             'lon_left': TMUT_CENTER_LON - BUFFER_GPS, 'lon_right': TMUT_CENTER_LON + BUFFER_GPS},
    'depot': {'lat_top': -3.57654, 'lat_bottom': -3.58654, 'lon_left': -38.84236, 'lon_right': -38.83236}
}

# --- CORREÇÃO: TEMPLATES MOVIDO PARA O ESCOPO GLOBAL ---
TEMPLATES = {
    'David': {
        'low_signal': [
            "Analisar histórico de sinal do <span class='copy-id' title='Clique para copiar'>{target}</span> nas últimas {horas} horas via MobiControl.",
            "Executar diagnóstico remoto de <span class='copy-id' title='Clique para copiar'>{target}</span> verificando logs de conectividade e perda de pacotes.",
            "Comparar performance do <span class='copy-id' title='Clique para copiar'>{target}</span> com outros tablets na área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a>.",
            "Reiniciar remotamente <span class='copy-id' title='Clique para copiar'>{target}</span> via MobiControl se persistir sinal abaixo do aceitável.",
            "Verificar aplicativos ou processos do <span class='copy-id' title='Clique para copiar'>{target}</span> que possam impactar a performance de rede."
        ],
        'packet_loss': [
            "Investigar perda de pacotes no <span class='copy-id' title='Clique para copiar'>{target}</span> conectando via MobiControl.",
            "Realizar teste de ping contínuo do <span class='copy-id' title='Clique para copiar'>{target}</span> para gateway para analisar estabilidade.",
            "Checar utilização do canal afetando o <span class='copy-id' title='Clique para copiar'>{target}</span>.",
            "Isolar <span class='copy-id' title='Clique para copiar'>{target}</span> em VLAN de teste para analisar causa da perda de pacotes.",
            "Analisar logs do switch relacionados ao <span class='copy-id' title='Clique para copiar'>{target}</span>."
        ],
        'offline': [
            "O <span class='copy-id' title='Clique para copiar'>{target}</span> está offline. Verificar logs de conexão e status remoto via MobiControl.",
            "Localizar <span class='copy-id' title='Clique para copiar'>{target}</span> usando última posição conhecida <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a> e confirmar conectividade.",
            "Investigar falha de hardware ou software no <span class='copy-id' title='Clique para copiar'>{target}</span> via MobiControl.",
            "Escalonar problema do <span class='copy-id' title='Clique para copiar'>{target}</span> se não houver resposta remota.",
            "Confirmar se o <span class='copy-id' title='Clique para copiar'>{target}</span> não foi desligado manualmente pelo operador." 
        ]
    },
    'Cleyton': {
        'low_signal': [
            "Realizar gemba na área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a> para medir cobertura.",
            "Verificar alinhamento de antenas e potência de transmissão afetando <span class='copy-id' title='Clique para copiar'>{target}</span>.",
            "Checar cabos e switches conectados na área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a>.",
            "Revisar posicionamento físico ou adicionar AP adicional se necessário.",
            "Documentar zona de baixa cobertura em <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a> para futuras otimizações."
        ],
        'packet_loss': [
            "Inspecionar fisicamente a área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a> em busca de interferências.",
            "Verificar cabos e conexões dos switches próximos.",
            "Executar medição de throughput para confirmar perda de pacotes.",
            "Ajustar canais para minimizar colisões e interferências.",
            "Agendar manutenção se persistir alta perda de pacotes."
        ],
        'offline': [
            "Verificar fisicamente na área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a> se <span class='copy-id' title='Clique para copiar'>{target}</span> estiver offline.",
            "Checar energia, cabos e conectividade dos equipamentos da área.",
            "Realizar inspeção preventiva em infraestrutura.",
            "Substituir hardware se houver falha persistente.",
            "Validar cobertura da rede no local para reduzir incidentes de offline."
        ]
    },
    'Wesley': {
        'coordination': [
            "Coordenar equipe de campo para resolver incidente com <span class='copy-id' title='Clique para copiar'>{target}</span> na área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{latitude}' data-lon='{longitude}'>{latitude},{longitude}</a>.",
            "Validar junto à operação se <span class='copy-id' title='Clique para copiar'>{target}</span> voltou a operar normalmente.",
            "Escalonar problema crítico do <span class='copy-id' title='Clique para copiar'>{target}</span> para gestão se necessário.",
            "Supervisionar execução do plano de ação envolvendo <span class='copy-id' title='Clique para copiar'>{target}</span>.",
            "Garantir que todas ações corretivas sejam documentadas e comunicadas."
        ],
        'proactive': [
            "Planejar revisão da cobertura de Wi-Fi nas áreas críticas do porto.",
            "Acompanhar indicadores de performance e incidentes do período {periodo}.",
            "Assegurar que todos tablets tenham políticas atualizadas no MobiControl.",
            "Avaliar histórico de incidentes para melhorar processos de manutenção.",
            "Revisar plano de contingência e protocolos de escalonamento de incidentes."
        ]
    }
}


# --- FUNÇÃO HELPER ---
def get_filtered_data(map_name=None, start_date=None, end_date=None, ssid_filter=None, tablet_id=None):
    df = database.get_all_raw_points()
    if df.empty:
        return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    if tablet_id:
        df = df[df['tablet_android_id'] == tablet_id]
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
        df = df[(df['latitude'].between(bounds['lat_bottom'], bounds['lat_top'])) &
                (df['longitude'].between(bounds['lon_left'], bounds['lon_right']))]
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
    tablet_id = request.args.get('tablet_id', None)
    df_filtered = get_filtered_data(map_name, start_date, end_date, ssid_filter, tablet_id)
    zones_data = analysis.generate_map_data(df_filtered)
    return jsonify(zones_data)

@app.route('/api/critical_points', methods=['GET'])
def critical_points_route():
    map_name = request.args.get('map', 'patio')
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    ssid_filter = request.args.get('ssid_filter', 'main_network')
    tablet_id = request.args.get('tablet_id', None)
    df_filtered = get_filtered_data(map_name, start_date, end_date, ssid_filter, tablet_id)
    chart_data = analysis.get_top_problem_locations(df_filtered)
    return jsonify(chart_data)

@app.route('/api/kpis', methods=['GET'])
def kpis_route():
    map_name = request.args.get('map', 'patio')
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    ssid_filter = request.args.get('ssid_filter', 'main_network')
    tablet_id = request.args.get('tablet_id', None)
    df_filtered = get_filtered_data(map_name, start_date, end_date, ssid_filter, tablet_id)
    kpi_data = analysis.calculate_kpis(df_filtered)
    return jsonify(kpi_data)

# --- ENDPOINT DE EXPORTAÇÃO ---
@app.route('/api/export', methods=['GET'])
def export_excel_route():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    ssid_filter = request.args.get('ssid_filter', None)
    tablet_id = request.args.get('tablet_id', None)

    if not start_date or not end_date:
        return "Erro: As datas de início e fim são obrigatórias.", 400

    df = get_filtered_data(start_date=start_date, end_date=end_date, ssid_filter=ssid_filter, tablet_id=tablet_id)
    if df.empty:
        return "Nenhum dado encontrado para os filtros selecionados.", 404

    def assign_area(row):
        lat, lon = row['latitude'], row['longitude']
        patio = MAPS_CONFIG['patio']
        tmut = MAPS_CONFIG['tmut']
        depot = MAPS_CONFIG['depot'] # Garanta que esta linha existe
        if (patio['lat_bottom'] <= lat <= patio['lat_top']) and (patio['lon_left'] <= lon <= patio['lon_right']):
            return 'Pátio'
        if (tmut['lat_bottom'] <= lat <= tmut['lat_top']) and (tmut['lon_left'] <= lon <= tmut['lon_right']):
            return 'TMUT'
        if (depot['lat_bottom'] <= lat <= depot['lat_top']) and (depot['lon_left'] <= lon <= depot['lon_right']):
            return 'Depot'
        return 'Fora da Área'
    
    df['Área'] = df.apply(assign_area, axis=1)
    df['Data'] = df['timestamp'].dt.strftime('%d/%m/%Y')
    df['Hora'] = df['timestamp'].dt.strftime('%H:%M:%S')

    column_mapping = {
        'tablet_android_id': 'Tablet (Android ID)',
        'signal_dbm': 'Sinal de Rede (dBm)',
        'current_ssid': 'Rede Wi-Fi Conectada',
        'packet_loss_percent': 'Perda de Pacotes (%)',
        'latitude': 'Latitude',
        'longitude': 'Longitude'
    }
    df_renamed = df.rename(columns=column_mapping)
    
    final_column_order = [
        'Tablet (Android ID)', 'Data', 'Hora', 'Área', 'Sinal de Rede (dBm)',
        'Rede Wi-Fi Conectada', 'Perda de Pacotes (%)', 'Latitude', 'Longitude'
    ]
    df_final = df_renamed[final_column_order]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for date_str, daily_data in df_final.groupby('Data'):
            sheet_name_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            sheet_name = sheet_name_date.strftime('%d-%m-%Y')
            sorted_daily_data = daily_data.sort_values(by=['Área', 'Rede Wi-Fi Conectada', 'Hora'])
            sorted_daily_data.to_excel(writer, sheet_name=sheet_name, index=False)
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

# --- FUNÇÃO DE GERAÇÃO DE AÇÕES ---
def get_point_value(point, key, fallback='N/A'):
    keys_map = {
        'latitude': ['latitude', 'lat', 'y'],
        'longitude': ['longitude', 'lon', 'lng', 'x'],
        'ssid': ['ssid', 'current_ssid', 'network']
    }
    for k in keys_map.get(key, [key]):
        if k in point and point[k] not in [None, '', 'N/A', '<unknown ssid>', 'disconnected']:
            return point[k]
    return fallback

def generate_actions(point, responsible):
    problem_type = point.get('issue', 'low_signal')
    templates = TEMPLATES.get(responsible, {}).get(problem_type, [])

    if not templates:
        return [f"Verificar <span class='copy-id' title='Clique para copiar'>{point.get('id','N/A')}</span> na área <a href='#' class='focus-location' title='Focar no mapa' data-lat='{get_point_value(point, 'latitude')}' data-lon='{get_point_value(point, 'longitude')}'>{get_point_value(point, 'latitude')},{get_point_value(point, 'longitude')}</a>"]

    num_actions = min(3, len(templates))
    selected_templates = random.sample(templates, num_actions)

    filled_actions = []
    for template in selected_templates:
        action = template.format(
            target=point.get('id','N/A'),
            ssid=get_point_value(point, 'ssid', 'desconhecido'),
            latitude=get_point_value(point, 'latitude'),
            longitude=get_point_value(point, 'longitude'),
            horas=random.choice([1,2,3,4,6]),
            periodo=point.get('periodo','período selecionado')
        )
        filled_actions.append(action)

    return filled_actions

@app.route('/api/analyze', methods=['POST'])
def analyze_route():
    try:
        time.sleep(random.uniform(1, 3))
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        map_data = data.get('map_data', {})
        context = data.get('context', {})
        
        analysis_result = analyze_wifi_data_robust(map_data, context)
        
        return jsonify({'analysis': analysis_result})
        
    except Exception as e:
        print(f"Erro na análise offline: {str(e)}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

def analyze_wifi_data_robust(map_data, context):
    critical_zones = map_data.get('critical_zones', [])
    attention_zones = map_data.get('attention_zones', [])
    good_zones = map_data.get('good_zones', [])

    problem_points = []
    for zone in critical_zones + attention_zones:
        problem_points.extend(zone['properties'].get('point_details', []))

    periodo = context.get('periodo', 'data selecionada')
    dispositivo = context.get('dispositivo', 'Todos os Dispositivos')

    if not problem_points and not critical_zones and not attention_zones and not good_zones:
        return f"""
### Diagnóstico e Oportunidade
Nenhuma medição disponível para o período de {periodo} em {dispositivo}.

**Sugestões:**
- Verifique se os tablets estão coletando dados corretamente.
- Certifique-se de que o período selecionado contém registros.
- Ajuste filtros de rede, área ou dispositivo, se necessário.
        """.strip()

    total_zones = len(critical_zones) + len(attention_zones) + len(good_zones)
    if not problem_points:
        status_text = "🟢 Excelente – não foram identificadas instabilidades."
    else:
        critical_count = len(critical_zones)
        attention_count = len(attention_zones)
        critical_ratio = critical_count / total_zones if total_zones else 0
        attention_ratio = attention_count / total_zones if total_zones else 0

        if critical_ratio > 0.3:
            status_text = "🔴 Crítico – muitas áreas com instabilidade."
        elif attention_ratio > 0.5 or critical_ratio > 0.15:
            status_text = "🟡 Atenção – instabilidade detectada."
        else:
            status_text = "🟢 Ótimo – rede com desempenho ótimo."

    worst_tablet_analysis = "Nenhum dispositivo se destaca."
    ssid_analysis = "Instabilidade distribuída de forma geral na rede principal."
    time_analysis = "Ocorrências distribuídas ao longo do dia."

    if problem_points:
        tablet_ids = [p['id'] for p in problem_points if 'id' in p]
        if tablet_ids:
            tablet_counts = Counter(tablet_ids)
            worst_tablet_id, worst_tablet_count = tablet_counts.most_common(1)[0]
            if worst_tablet_count > len(problem_points) * 0.4:
                worst_tablet_analysis = (
                    f"O tablet <span class='copy-id' title='Clique para copiar'>{worst_tablet_id}</span> foi "
                    f"responsável por **{worst_tablet_count}** de {len(problem_points)} incidentes."
                )
            else:
                worst_tablet_analysis = "As instabilidades estão distribuídas entre vários dispositivos."

        ssids = [p.get('ssid', 'desconhecido') for p in problem_points]
        ssid_counts = Counter(ssids)
        disconnected_count = ssid_counts.get('disconnected', 0) + ssid_counts.get('<unknown ssid>', 0)
        if disconnected_count > len(problem_points) * 0.5:
            ssid_analysis = f"O ponto principal de otimização é tratar as **{disconnected_count} quedas totais de conexão**."

        hours = []
        for p in problem_points:
            try:
                hour = int(p['time'].split(' ')[1].split(':')[0])
                hours.append(hour)
            except:
                pass
        if hours:
            hour_counts = Counter(hours)
            madrugada = sum(count for hour, count in hour_counts.items() if 0 <= hour < 6)
            manha = sum(count for hour, count in hour_counts.items() if 6 <= hour < 12)
            tarde = sum(count for hour, count in hour_counts.items() if 12 <= hour < 18)
            noite = sum(count for hour, count in hour_counts.items() if 18 <= hour <= 23)
            periodos = {'Madrugada (00h-06h)': madrugada, 'Manhã (06h-12h)': manha, 'Tarde (12h-18h)': tarde, 'Noite (18h-00h)': noite}
            periodo_pico = max(periodos, key=periodos.get)
            if periodos[periodo_pico] > len(hours) * 0.5:
                time_analysis = f"Há concentração de eventos no período da **{periodo_pico.split(' ')[0]}**."
    
    # O DICIONÁRIO TEMPLATES FOI MOVIDO DAQUI PARA CIMA (ESCOPO GLOBAL)

    planos_de_acao = []
    if problem_points:
        unique_actions = set()
        
        points_to_process = random.sample(problem_points, min(len(problem_points), 10))
        
        for point in points_to_process:
            unique_actions.update(generate_actions(point, 'David'))
            unique_actions.update(generate_actions(point, 'Cleyton'))
            unique_actions.update(generate_actions(point, 'Wesley'))
        
        planos_de_acao = list(unique_actions)
        
        if len(planos_de_acao) > 3:
            planos_de_acao = random.sample(planos_de_acao, 3)
    else:
        planos_de_acao = generate_actions({'id':'todos','latitude':TMUT_CENTER_LAT,'longitude':TMUT_CENTER_LON,'periodo':periodo,'issue':'proactive'}, 'Wesley')

    diagnostico = f"**Status Geral da Rede:** {status_text}\n**Período analisado:** {periodo}\n**Dispositivo analisado:** {dispositivo}\n**Total de incidentes:** {len(problem_points)}"
    report = f"### Diagnóstico e Oportunidade\n{diagnostico}\n\n### Focos de Otimização\n- **Dispositivo Chave:** {worst_tablet_analysis}\n- **Ponto de Otimização na Rede:** {ssid_analysis}\n- **Padrão de Horário:** {time_analysis}\n\n### Plano de Ação\n"
    for rec in planos_de_acao:
        report += f"- {rec}\n"

    return report.strip()

if __name__ == '__main__':
    print("Iniciando servidor de produção na porta 5000...")
    serve(app, host='0.0.0.0', port=5000)