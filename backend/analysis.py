import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
import math

# scipy.spatial.ConvexHull não é mais necessário
# from scipy.spatial import ConvexHull 

EPSILON_METERS = 35 
MIN_SAMPLES = 1
GRID_SIZE_GPS = 0.0002

def classify_point_status(row):
    """Função única e centralizada para classificar um ponto."""
    if row['signal_dbm'] <= -85 or row['packet_loss_percent'] > 3:
        return 'critical'
    if row['signal_dbm'] <= -70:
        return 'attention'
    return 'good'

def create_zones_from_points(points, status):
    """Função de clusterização ATUALIZADA com a nova lógica de raio e opacidade."""
    if not points:
        return []
    coords_list = [{'lng': p['lng'], 'lat': p['lat']} for p in points]
    coords = np.array([[p['lng'], p['lat']] for p in coords_list])
    if len(coords) == 0:
        return []

    avg_lat_rad = math.radians(np.mean(coords[:, 1]))
    epsilon_in_degrees = EPSILON_METERS / (111132.954 * math.cos(avg_lat_rad))
    db = DBSCAN(eps=epsilon_in_degrees, min_samples=MIN_SAMPLES).fit(coords)
    labels = db.labels_
    
    zones = []
    for label in set(labels):
        cluster_points = coords[labels == label]
        point_count = len(cluster_points)

        # --- NOVA LÓGICA DE RAIO E OPACIDADE ---

        # 1. Define o RAIO (tamanho) com base na contagem de pontos
        if point_count == 1:
            radius = 10  # Tamanho Pequeno
        elif point_count == 2:
            radius = 15  # Tamanho Médio
        else: # 3 ou mais pontos
            radius = 20  # Tamanho Grande (máximo)

        # 2. Define a OPACIDADE (gravidade)
        opacity = 0.4 # Padrão para pontos 'good'
        if status == 'attention':
            base_opacity = 0.5
            if point_count <= 2:
                opacity = base_opacity
            else: # Aumenta progressivamente de 3 a 10 pontos
                opacity = np.interp(point_count, [3, 10], [0.65, 0.9])
        elif status == 'critical':
            base_opacity = 0.6
            if point_count <= 2:
                opacity = base_opacity
            else: # Aumenta progressivamente de 3 a 10 pontos
                opacity = np.interp(point_count, [3, 10], [0.75, 1.0])

        # 3. Cria a feature SEMPRE como um Ponto (círculo)
        centroid = np.mean(cluster_points, axis=0)
        feature = {
            "type": "Feature",
            "properties": {
                "status": status,
                "point_count": point_count,
                "radius": radius,
                "opacity": round(opacity, 2) # Envia a opacidade calculada
            },
            "geometry": {
                "type": "Point",
                "coordinates": centroid.tolist()
            }
        }
        zones.append(feature)
    return zones

# As funções abaixo não precisam de alteração
def generate_map_data(df):
    # ... (código inalterado) ...
    if df.empty: return {'critical_zones': [], 'attention_zones': [], 'good_zones': []}
    df['status'] = df.apply(classify_point_status, axis=1)
    points_data = {
        'critical': df[df['status'] == 'critical'].rename(columns={'latitude': 'lat', 'longitude': 'lng'}).to_dict('records'),
        'attention': df[df['status'] == 'attention'].rename(columns={'latitude': 'lat', 'longitude': 'lng'}).to_dict('records'),
        'good': df[df['status'] == 'good'].rename(columns={'latitude': 'lat', 'longitude': 'lng'}).to_dict('records')
    }
    critical_zones = create_zones_from_points(points_data['critical'], 'critical')
    attention_zones = create_zones_from_points(points_data['attention'], 'attention')
    good_zones = create_zones_from_points(points_data['good'], 'good')
    return {'critical_zones': critical_zones, 'attention_zones': attention_zones, 'good_zones': good_zones}

def get_top_critical_points(df):
    # ... (código inalterado) ...
    if df.empty: return {'labels': [], 'datasets': []}
    df['status'] = df.apply(classify_point_status, axis=1)
    df['is_bad'] = df['status'].apply(lambda s: 1 if s in ['critical', 'attention'] else 0)
    df['grid_lat'] = (df['latitude'] // GRID_SIZE_GPS).astype(int)
    df['grid_lon'] = (df['longitude'] // GRID_SIZE_GPS).astype(int)
    df['grid_id'] = df['grid_lat'].astype(str) + '_' + df['grid_lon'].astype(str)
    grid_agg = df.groupby('grid_id').agg(avg_lat=('latitude', 'mean'), avg_lon=('longitude', 'mean'), total_points=('tablet_android_id', 'count'), bad_points=('is_bad', 'sum')).reset_index()
    grid_agg = grid_agg[grid_agg['bad_points'] > 0]
    top_10 = grid_agg.sort_values(by='bad_points', ascending=False).head(10)
    chart_data = {
        'labels': [f"{i+1}º" for i in range(len(top_10))],
        'datasets': [{'label': 'Quantidade de Medições Ruins', 'data': top_10['bad_points'].tolist(),
            'full_data': [{'grid_id': r['grid_id'], 'total': r['total_points'], 'bad': r['bad_points'], 'lat': r['avg_lat'], 'lng': r['avg_lon']} for i, r in top_10.iterrows()]
        }]
    }
    return chart_data