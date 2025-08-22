import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
import math

# --- CONSTANTES GLOBAIS ---
EPSILON_METERS = 35
MIN_SAMPLES = 1
GRID_SIZE_GPS = 0.0002

# --- FUNÇÕES DE ANÁLISE ---

def classify_point_status(row):
    """Função única e centralizada para classificar um ponto."""
    if row['signal_dbm'] <= -85 or row['packet_loss_percent'] > 3:
        return 'critical'
    if row['signal_dbm'] <= -70:
        return 'attention'
    return 'good'

def create_zones_from_points(points_df, status):
    """
    Função de clusterização ATUALIZADA para incluir detalhes dos pontos.
    Agora recebe um DataFrame do Pandas.
    """
    if points_df.empty:
        return []

    coords = points_df[['lng', 'lat']].values
    if len(coords) == 0:
        return []

    avg_lat_rad = math.radians(coords[:, 1].mean())
    epsilon_in_degrees = EPSILON_METERS / (111132.954 * math.cos(avg_lat_rad))
    db = DBSCAN(eps=epsilon_in_degrees, min_samples=MIN_SAMPLES).fit(coords)
    labels = db.labels_

    zones = []
    for label in set(labels):
        # Seleciona os pontos do cluster atual
        cluster_mask = (labels == label)
        cluster_df = points_df[cluster_mask]
        cluster_points_coords = coords[cluster_mask]
        point_count = len(cluster_df)

        # LÓGICA DE RAIO E OPACIDADE (inalterada)
        if point_count == 1:
            radius = 10
        elif point_count == 2:
            radius = 15
        else:
            radius = 20

        opacity = 0.4
        if status == 'attention':
            base_opacity = 0.5
            opacity = np.interp(point_count, [1, 10], [base_opacity, 0.9]) if point_count > 1 else base_opacity
        elif status == 'critical':
            base_opacity = 0.6
            opacity = np.interp(point_count, [1, 10], [base_opacity, 1.0]) if point_count > 1 else base_opacity

        # --- NOVA LÓGICA: Coleta de detalhes ---
        point_details = []
        for _, row in cluster_df.iterrows():
            point_details.append({
                'id': row['tablet_android_id'],
                # Formata o timestamp para mostrar apenas a hora
                'time': pd.to_datetime(row['timestamp']).strftime('%H:%M:%S')
            })

        centroid = np.mean(cluster_points_coords, axis=0)
        feature = {
            "type": "Feature",
            "properties": {
                "status": status,
                "point_count": point_count,
                "radius": radius,
                "opacity": round(opacity, 2),
                "point_details": point_details  # Adiciona os detalhes ao GeoJSON
            },
            "geometry": { "type": "Point", "coordinates": centroid.tolist() }
        }
        zones.append(feature)
    return zones

def generate_map_data(df):
    """Prepara os dados para a visualização do mapa, separando por status."""
    if df.empty:
        return {'critical_zones': [], 'attention_zones': [], 'good_zones': []}

    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    df_copy.rename(columns={'latitude': 'lat', 'longitude': 'lng'}, inplace=True)

    # Converte para DataFrame para passar para a função de clusterização
    critical_df = pd.DataFrame(df_copy[df_copy['status'] == 'critical'])
    attention_df = pd.DataFrame(df_copy[df_copy['status'] == 'attention'])
    good_df = pd.DataFrame(df_copy[df_copy['status'] == 'good'])

    critical_zones = create_zones_from_points(critical_df, 'critical')
    attention_zones = create_zones_from_points(attention_df, 'attention')
    good_zones = create_zones_from_points(good_df, 'good')

    return {'critical_zones': critical_zones, 'attention_zones': attention_zones, 'good_zones': good_zones}

# --- FUNÇÃO DO GRÁFICO TOP 10 (ATUALIZADA) ---
def get_top_problem_locations(df):
    if df.empty:
        return []

    df_copy = df.copy()
    df_copy['status'] = df_copy.apply(classify_point_status, axis=1)
    df_copy['grid_lat'] = (df_copy['latitude'] // GRID_SIZE_GPS).astype(int)
    df_copy['grid_lon'] = (df_copy['longitude'] // GRID_SIZE_GPS).astype(int)
    df_copy['grid_id'] = df_copy['grid_lat'].astype(str) + '_' + df_copy['grid_lon'].astype(str)

    problem_points = df_copy[df_copy['status'].isin(['critical', 'attention'])].copy()
    if problem_points.empty:
        return []

    counts = problem_points.groupby(['grid_id', 'status']).size()
    counts_df = counts.unstack(fill_value=0)

    if 'critical' not in counts_df.columns:
        counts_df['critical'] = 0
    if 'attention' not in counts_df.columns:
        counts_df['attention'] = 0

    counts_df['total_problems'] = counts_df['critical'] + counts_df['attention']
    top_10 = counts_df.sort_values(by='total_problems', ascending=False).head(10)
    
    # Versão otimizada para encontrar a coordenada do ponto mais grave
    top_10_grids = top_10.index
    top_points = problem_points[problem_points['grid_id'].isin(top_10_grids)].copy()
    top_points['status_cat'] = pd.Categorical(top_points['status'], categories=['critical', 'attention'], ordered=True)
    top_points.sort_values('status_cat', inplace=True)
    coords_df = top_points.drop_duplicates(subset='grid_id', keep='first')[['grid_id', 'latitude', 'longitude']]
    coords_df.set_index('grid_id', inplace=True)
    coords_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)

    final_top_10 = top_10.join(coords_df)
    final_top_10.reset_index(inplace=True)
    final_top_10.rename(columns={'critical': 'critical_count', 'attention': 'attention_count'}, inplace=True)

    return final_top_10.to_dict(orient='records')