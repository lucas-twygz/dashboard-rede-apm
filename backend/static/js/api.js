// A constante API_BASE_URL foi removida.

export async function fetchMapData(mapName, startDate, endDate, ssidFilter) {
    const params = new URLSearchParams({ map: mapName, ssid_filter: ssidFilter });
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    const response = await fetch(`/api/map_data?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de dados do mapa: ${response.status}`);
    return await response.json();
}

export async function fetchCriticalPoints(mapName, startDate, endDate, ssidFilter) {
    const params = new URLSearchParams({ map: mapName, ssid_filter: ssidFilter });
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    const response = await fetch(`/api/critical_points?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de pontos críticos: ${response.status}`);
    return await response.json();
}

// --- NOVA FUNÇÃO PARA BUSCAR KPIs ---
export async function fetchKpis(mapName, startDate, endDate, ssidFilter) {
    const params = new URLSearchParams({ map: mapName, ssid_filter: ssidFilter });
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    const response = await fetch(`/api/kpis?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de KPIs: ${response.status}`);
    return await response.json();
}