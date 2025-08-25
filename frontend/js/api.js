const API_BASE_URL = 'http://127.0.0.1:5000/api';

export async function fetchMapData(mapName, startDate, endDate) {
    const params = new URLSearchParams({ map: mapName });
    
    // Adiciona os parâmetros de data apenas se eles existirem
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }

    const response = await fetch(`${API_BASE_URL}/map_data?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de dados do mapa: ${response.status}`);
    return await response.json();
}

export async function fetchCriticalPoints(mapName, startDate, endDate) {
    const params = new URLSearchParams({ map: mapName });

    // Adiciona os parâmetros de data apenas se eles existirem
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    
    const response = await fetch(`${API_BASE_URL}/critical_points?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de pontos críticos: ${response.status}`);
    return await response.json();
}