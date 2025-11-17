import numpy as np
import pandas as pd
import math

# --- CONSTANTES GLOBAIS ---
# O GRID_SIZE_GPS não será mais usado para agrupar, mas o mantemos caso seja útil para outras funções.
GRID_SIZE_GPS = 0.00025

# --- FUNÇÕES DE ANÁLISE ---
def classify_point_status(row):
    """Função única e centralizada para classificar um ponto."""
    if row['signal_dbm'] <= -85 or row['packet_loss_percent'] > 3:
        return 'critical'
    if row['signal_dbm'] <= -70:
        return 'attention'
    return 'good'

def create_individual_points(points_df, status):
    """
    NOVA FUNÇÃO: Transforma cada ponto de dados em um 'Feature' GeoJSON individual para plotagem.
    Cada ponto será uma zona, sem agrupamento.
    """
    if points_df.empty:
        return []

    zones = []
    for index, row in points_df.iterrows():
        # Define um raio e opacidade fixos para melhor visualização de pontos individuais
        radius, opacity = 5, 0.9

        timestamp = pd.to_datetime(row['timestamp'])
        formatted_time = timestamp.strftime('%d/%m/%Y %H:%M:%S')

        point_details = [{
            'id': row['tablet_android_id'],
            'time': formatted_time,
            'ssid': row['current_ssid'],
            'lat': row['lat'],
            'lon': row['lng']
        }]

        # As coordenadas da geometria agora são do próprio ponto
        centroid = [row['lng'], row['lat']]

        feature = {
            "type": "Feature",
            "properties": {
                "status": status,
                "point_count": 1, # Cada "zona" agora tem apenas 1 ponto
                "opacity": opacity,
                "radius": radius,
                "point_details": point_details
            },
            "geometry": {
                "type": "Point",
                "coordinates": centroid
            }
        }
        zones.append(feature)
    return zones

def generate_map_data(df):
    if df.empty:
        return {'critical_zones': [], 'attention_zones': [], 'good_zones': []}
    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    df_copy.rename(columns={'latitude': 'lat', 'longitude': 'lng'}, inplace=True)

    critical_df, attention_df, good_df = [df_copy[df_copy['status'] == s] for s in ['critical', 'attention', 'good']]

    return {
        'critical_zones': create_individual_points(critical_df, 'critical'),
        'attention_zones': create_individual_points(attention_df, 'attention'),
        'good_zones': create_individual_points(good_df, 'good')
    }

# --- LÓGICA DO GRÁFICO (CORRIGIDA) ---
def get_top_problem_locations(df):
    if df.empty:
        return []

    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)

    # Inclui todos os status: critical, attention e good
    problem_points = df_copy[df_copy['status'].isin(['critical', 'attention', 'good'])].copy()
    if problem_points.empty:
        return []

    problem_points['grid_lat'] = (problem_points['latitude'] // GRID_SIZE_GPS).astype(int)
    problem_points['grid_lon'] = (problem_points['longitude'] // GRID_SIZE_GPS).astype(int)

    # Agrupa por grid e status
    counts = problem_points.groupby(['grid_lat', 'grid_lon', 'status']).size().unstack(fill_value=0)

    # Garante que todas as colunas existam
    for col in ['critical', 'attention', 'good']:
        if col not in counts.columns:
            counts[col] = 0

    counts['total_problems'] = counts['critical'] + counts['attention'] + counts['good']
    counts.reset_index(inplace=True)

    visited = set()
    clusters = []
    grid_coords = set(zip(counts['grid_lat'], counts['grid_lon']))

    # Agrupamento de grids vizinhos
    for index, grid in counts.iterrows():
        lat, lon = grid['grid_lat'], grid['grid_lon']
        if (lat, lon) in visited:
            continue
        current_cluster_coords = set()
        q = [(lat, lon)]
        visited.add((lat, lon))
        while q:
            current_lat, current_lon = q.pop(0)
            current_cluster_coords.add((current_lat, current_lon))
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == 0 and j == 0:
                        continue
                    neighbor = (current_lat + i, current_lon + j)
                    if neighbor in grid_coords and neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)
        clusters.append(current_cluster_coords)

    # Monta os dados finais para o gráfico
    clustered_data = []
    for i, cluster_coords in enumerate(clusters):
        cluster_df = counts[counts.set_index(['grid_lat', 'grid_lon']).index.isin(cluster_coords)]
        cluster_points = problem_points[problem_points.set_index(['grid_lat', 'grid_lon']).index.isin(cluster_coords)]

        critical_count = cluster_df['critical'].sum()
        attention_count = cluster_df['attention'].sum()
        good_count = cluster_df['good'].sum()

        avg_lat = cluster_points['latitude'].mean()
        avg_lon = cluster_points['longitude'].mean()

        clustered_data.append({
            'grid_id': f'{i+1}',
            'critical_count': int(critical_count),
            'attention_count': int(attention_count),
            'good_count': int(good_count),
            'total_problems': int(critical_count + attention_count + good_count),
            'lat': avg_lat,
            'lon': avg_lon
        })

    # Ordena do pior para o melhor, mas mantém sempre até 10 clusters
    final_top_10 = sorted(clustered_data, key=lambda x: x['total_problems'], reverse=True)[:10]

    return final_top_10

# --- FUNÇÃO DE KPIs ---
def calculate_kpis(df):
    if df.empty:
        return { 
            'total_measurements': 0, 
            'critical_percentage': 0, 
            'disconnections': 0, 
            'worst_tablet': 'N/A',
            'unique_devices': 0,
            'avg_signal': 0,            # Adicionado
            'avg_latency': 'N/A',       # Adicionado
            'peak_problem_hour': 'N/A'  # Adicionado
        }
    
    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    
    # --- Cálculos existentes ---
    total_measurements = len(df_copy)
    critical_count = df_copy[df_copy['status'] == 'critical'].shape[0]
    critical_percentage = (critical_count / total_measurements) * 100 if total_measurements > 0 else 0
    disconnections = df_copy[df_copy['current_ssid'] == 'disconnected'].shape[0]
    unique_devices = df_copy['tablet_android_id'].nunique()

    worst_tablet = 'N/A'
    problem_points = df_copy[df_copy['status'].isin(['critical', 'attention'])]
    if not problem_points.empty:
        tablet_counts = problem_points['tablet_android_id'].value_counts()
        if not tablet_counts.empty:
            worst_tablet = tablet_counts.index[0]
            
    # --- NOVOS CÁLCULOS DE KPI ---
    
    # 1. Sinal Médio (dBm)
    avg_signal = df_copy['signal_dbm'].mean()
    
    # 2. Latência Média (ms) - Verifica se a coluna existe
    avg_latency_kpi = 'N/A'
    if 'latency_ms' in df_copy.columns and pd.api.types.is_numeric_dtype(df_copy['latency_ms']):
        # Calcula a média apenas de valores válidos (maiores que 0)
        valid_latency = df_copy[df_copy['latency_ms'] > 0]['latency_ms']
        if not valid_latency.empty:
            avg_latency = valid_latency.mean()
            avg_latency_kpi = round(avg_latency, 0)

    # 3. Horas com Maior Incidência de Problemas
    peak_problem_hour_kpi = 'N/A'
    if not problem_points.empty:
        # Extrai a hora da coluna timestamp (que já deve ser datetime)
        hours = problem_points['timestamp'].dt.hour
        if not hours.empty:
            peak_hour = hours.value_counts().idxmax()
            # Formata como "14:00 - 15:00"
            peak_problem_hour_kpi = f"{int(peak_hour):02d}:00 - {int(peak_hour) + 1:02d}:00"

    # --- Retorno atualizado ---
    return {
        'total_measurements': total_measurements,
        'critical_percentage': round(critical_percentage, 1),
        'disconnections': disconnections,
        'worst_tablet': worst_tablet,
        'unique_devices': unique_devices,
        'avg_signal': round(avg_signal, 1) if not pd.isna(avg_signal) else 0, # Adicionado
        'avg_latency': avg_latency_kpi,                                     # Adicionado
        'peak_problem_hour': peak_problem_hour_kpi                          # Adicionado
    }