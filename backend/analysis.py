import numpy as np
import pandas as pd
import math

# --- CONSTANTES GLOBAIS ---
GRID_SIZE_GPS = 0.00025 

# --- FUNÇÕES DE ANÁLISE ---
def classify_point_status(row):
    """Função única e centralizada para classificar um ponto."""
    if row['signal_dbm'] <= -85 or row['packet_loss_percent'] > 3:
        return 'critical'
    if row['signal_dbm'] <= -70:
        return 'attention'
    return 'good'

def create_grid_zones(points_df, status):
    if points_df.empty: return []
    df = points_df.copy()
    df['grid_lat'] = (df['lat'] // GRID_SIZE_GPS)
    df['grid_lon'] = (df['lng'] // GRID_SIZE_GPS)
    df['grid_id'] = df['grid_lat'].astype(str) + '_' + df['grid_lon'].astype(str)
    zones = []
    for grid_id, group in df.groupby('grid_id'):
        point_count = len(group)
        if status == 'good':
            radius, opacity = 7, 0.15
        else:
            if point_count == 1: radius = 10
            elif point_count < 5: radius = 15
            else: radius = 20
            opacity = 0.4
            if status == 'attention':
                base_opacity = 0.5
                opacity = np.interp(point_count, [1, 10], [base_opacity, 0.9]) if point_count > 1 else base_opacity
            elif status == 'critical':
                base_opacity = 0.6
                opacity = np.interp(point_count, [1, 10], [base_opacity, 1.0]) if point_count > 1 else base_opacity
        point_details = []
        for index, row in group.iterrows():
            timestamp = pd.to_datetime(row['timestamp'])
            formatted_time = timestamp.strftime('%d/%m/%Y %H:%M:%S')
            point_details.append({ 'id': row['tablet_android_id'], 'time': formatted_time, 'ssid': row['current_ssid'] })
        centroid = [group['lng'].mean(), group['lat'].mean()]
        feature = {
            "type": "Feature",
            "properties": { "status": status, "point_count": point_count, "radius": radius, "opacity": round(opacity, 2), "point_details": point_details },
            "geometry": { "type": "Point", "coordinates": centroid }
        }
        zones.append(feature)
    return zones

def generate_map_data(df):
    if df.empty: return {'critical_zones': [], 'attention_zones': [], 'good_zones': []}
    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    df_copy.rename(columns={'latitude': 'lat', 'longitude': 'lng'}, inplace=True)
    critical_df, attention_df, good_df = [df_copy[df_copy['status'] == s] for s in ['critical', 'attention', 'good']]
    return {
        'critical_zones': create_grid_zones(critical_df, 'critical'),
        'attention_zones': create_grid_zones(attention_df, 'attention'),
        'good_zones': create_grid_zones(good_df, 'good')
    }

# --- LÓGICA DO GRÁFICO (CORRIGIDA) ---
def get_top_problem_locations(df):
    if df.empty: return []
    
    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    problem_points = df_copy[df_copy['status'].isin(['critical', 'attention'])].copy()
    if problem_points.empty: return []

    problem_points['grid_lat'] = (problem_points['latitude'] // GRID_SIZE_GPS).astype(int)
    problem_points['grid_lon'] = (problem_points['longitude'] // GRID_SIZE_GPS).astype(int)
    
    counts = problem_points.groupby(['grid_lat', 'grid_lon', 'status']).size().unstack(fill_value=0)
    if 'critical' not in counts.columns: counts['critical'] = 0
    if 'attention' not in counts.columns: counts['attention'] = 0
    counts['total_problems'] = counts['critical'] + counts['attention']
    counts.reset_index(inplace=True)

    visited = set()
    clusters = []
    grid_coords = set(zip(counts['grid_lat'], counts['grid_lon']))

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
                    if i == 0 and j == 0: continue
                    neighbor = (current_lat + i, current_lon + j)
                    if neighbor in grid_coords and neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)
        clusters.append(current_cluster_coords)

    clustered_data = []
    for i, cluster_coords in enumerate(clusters):
        cluster_df = counts[counts.set_index(['grid_lat', 'grid_lon']).index.isin(cluster_coords)]
        
        critical_count = cluster_df['critical'].sum()
        attention_count = cluster_df['attention'].sum()
        
        # --- CORREÇÃO APLICADA AQUI ---
        # 1. Pega TODOS os pontos originais que pertencem a este cluster
        cluster_points = problem_points[problem_points.set_index(['grid_lat', 'grid_lon']).index.isin(cluster_coords)]
        
        # 2. Calcula o centroide (média) das coordenadas desses pontos
        avg_lat = cluster_points['latitude'].mean()
        avg_lon = cluster_points['longitude'].mean()
        # --- FIM DA CORREÇÃO ---

        clustered_data.append({
            'grid_id': f'{i+1}',
            'critical_count': int(critical_count),
            'attention_count': int(attention_count),
            'total_problems': int(critical_count + attention_count),
            'lat': avg_lat, # Usa a latitude média
            'lon': avg_lon  # Usa a longitude média
        })

    final_top_10 = sorted(clustered_data, key=lambda x: x['total_problems'], reverse=True)[:10]
    
    return final_top_10

# --- FUNÇÃO DE KPIs ---
def calculate_kpis(df):
    if df.empty:
        return { 'total_measurements': 0, 'critical_percentage': 0, 'disconnections': 0, 'worst_tablet': 'N/A' }
    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    total_measurements = len(df_copy)
    critical_count = df_copy[df_copy['status'] == 'critical'].shape[0]
    critical_percentage = (critical_count / total_measurements) * 100 if total_measurements > 0 else 0
    disconnections = df_copy[df_copy['current_ssid'] == 'disconnected'].shape[0]
    worst_tablet = 'N/A'
    problem_points = df_copy[df_copy['status'].isin(['critical', 'attention'])]
    if not problem_points.empty:
        tablet_counts = problem_points['tablet_android_id'].value_counts()
        if not tablet_counts.empty:
            worst_tablet = tablet_counts.index[0]
    return {
        'total_measurements': total_measurements,
        'critical_percentage': round(critical_percentage, 1),
        'disconnections': disconnections,
        'worst_tablet': worst_tablet
    }