from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import database
import analysis
import pandas as pd
import io
import json # <-- NOVO: Para manipular o JSON dos dados
import requests # <-- NOVO: Para fazer a chamada à API da OpenRouter

# Adicionado para o Waitress
from waitress import serve

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
def get_filtered_data(map_name=None, start_date=None, end_date=None, ssid_filter=None, tablet_id=None):
    df = database.get_all_raw_points()
    if df.empty: return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    if tablet_id:
        df = df[df['tablet_android_id'] == tablet_id]
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

# <-- NOVO: ENDPOINT PARA ANÁLISE COM IA -->
@app.route('/api/analyze', methods=['POST'])
def analyze_data_route():
    """
    Recebe os dados do mapa do frontend, consulta a IA da OpenRouter e retorna a análise.
    """
    OPENROUTER_API_KEY = "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"
    
    request_data = request.json
    map_data = request_data.get('map_data', {})
    context = request_data.get('context', {})

    prompt_template = """
**PERSONA E OBJETIVO:**

Você é um Analista de Redes Sênior, especialista em otimização de Wi-Fi em terminais portuários. Sua missão é analisar os dados de conectividade abaixo e gerar um relatório **extremamente resumido, acionável e com foco construtivo** para a equipe de TI local da APM Terminals em Pecém.

**Adote um tom 100% construtivo e profissional. Encare os dados não como "falhas", mas como OPORTUNIDADES claras de otimização para tornar a rede ainda mais robusta.** Seja direto, técnico e use frases curtas ou bullet points.

**BACKGROUND E CONTEXTO OPERACIONAL:**

* **Ambiente:** Terminal de contêineres onde a estabilidade do Wi-Fi é crucial para a operação.
* **Sistemas Críticos:** A rede suporta o sistema **Navis N4 (TOS)** nos tablets dos operadores.
* **Equipe de TI:** O relatório é para **Cleyton (Campo)**, **David (Sistemas/MobiControl)**, e **Wesley (Gerente)**. Suas recomendações devem ser direcionadas a eles.

**FOCO E ADAPTAÇÃO DA ANÁLISE:**

Sua tarefa é analisar os dados de `critical_zones` à luz do `CONTEXTO DA ANÁLISE` fornecido abaixo. **Você deve iniciar sua resposta mencionando este contexto.**

**INSTRUÇÕES DETALHADAS (SEJA BREVE E ADAPTATIVO):**

1.  **Diagnóstico:** Comece declarando o contexto da análise. De seguida, numa única frase, identifique a **principal oportunidade de otimização** revelada pelos dados e o seu potencial impacto positivo na operação.
2.  **Análise de Causa Raiz:** Usando bullet points, analise os dados para identificar os principais focos de otimização:
    * **Dispositivo(s) Chave:** Qual tablet (`id`) oferece a maior oportunidade de melhoria através de uma verificação?
    * **Ponto de Otimização na Rede:** A maior oportunidade está em estabilizar uma rede específica ou em tratar quedas totais (`disconnected`)? O que isso sugere?
    * **Padrão de Horário:** Existe algum período do dia (`time`) onde as otimizações teriam maior impacto?
3.  **Plano de Ação (Recomendações):** Crie uma lista de ações diretas e específicas, adaptadas ao contexto.

**FORMATO DA RESPOSTA:**

Use o seguinte template em Markdown. Mantenha-o enxuto.

```markdown
### Diagnóstico

### 💡 Focos de Otimização

### 🚀 Plano de Ação
```

---
**CONTEXTO DA ANÁLISE:**

* **Período de Análise:** {periodo}
* **Dispositivo(s) Analisado(s):** {dispositivo}

**DADOS PARA ANÁLISE:**

```json
{json_data}
```
"""
    
    final_prompt = prompt_template.format(
        periodo=context.get('periodo', 'Não especificado'),
        dispositivo=context.get('dispositivo', 'Todos os Dispositivos'),
        json_data=json.dumps(map_data, indent=2)
    )
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-4-scout:free",
                "messages": [
                    {"role": "user", "content": final_prompt}
                ]
            }
        )
        response.raise_for_status()
        
        ai_response = response.json()['choices'][0]['message']['content']
        
        return jsonify({"analysis": ai_response})

    except requests.exceptions.RequestException as e:
        print(f"Erro ao contactar a API da OpenRouter: {e}")
        error_details = str(e)
        if e.response is not None:
            error_details = e.response.text
        return jsonify({"error": "Não foi possível obter a análise da IA.", "details": error_details}), 500


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

# --- ENDPOINT DE EXPORTAÇÃO (CORRIGIDO) ---
@app.route('/api/export', methods=['GET'])
def export_excel_route():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    # --- NOVOS PARÂMETROS ADICIONADOS ---
    ssid_filter = request.args.get('ssid_filter', None)
    tablet_id = request.args.get('tablet_id', None)

    if not start_date or not end_date:
        return "Erro: As datas de início e fim são obrigatórias.", 400

    # A função agora recebe TODOS os filtros
    df = get_filtered_data(start_date=start_date, end_date=end_date, ssid_filter=ssid_filter, tablet_id=tablet_id)
    if df.empty:
        return "Nenhum dado encontrado para os filtros selecionados.", 404

    def assign_area(row):
        lat, lon = row['latitude'], row['longitude']
        patio = MAPS_CONFIG['patio']
        tmut = MAPS_CONFIG['tmut']
        if (patio['lat_bottom'] <= lat <= patio['lat_top']) and (patio['lon_left'] <= lon <= patio['lon_right']):
            return 'Pátio'
        if (tmut['lat_bottom'] <= lat <= tmut['lat_top']) and (tmut['lon_left'] <= lon <= tmut['lon_right']):
            return 'TMUT'
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

# --- INICIALIZAÇÃO PARA PRODUÇÃO ---
if __name__ == '__main__':
    print("Iniciando servidor de produção na porta 5000...")
    serve(app, host='0.0.0.0', port=5000)