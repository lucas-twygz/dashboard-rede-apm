const API_BASE_URL = 'http://127.0.0.1:5000/api';

export async function fetchMapData() {
    const response = await fetch(`${API_BASE_URL}/map_data`);
    if (!response.ok) throw new Error(`Falha na API de dados do mapa: ${response.status}`);
    return await response.json();
}

export async function fetchCriticalPoints(mapName) {
    const response = await fetch(`${API_BASE_URL}/critical_points?map=${mapName}`);
    if (!response.ok) throw new Error(`Falha na API de pontos críticos: ${response.status}`);
    return await response.json();
}