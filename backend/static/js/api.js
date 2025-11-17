/**
 * Adiciona parâmetros de hora à URL se eles existirem.
 * @param {URLSearchParams} params - O objeto de parâmetros da URL.
 * @param {string|null} startHour - A hora inicial (ou null).
 * @param {string|null} endHour - A hora final (ou null).
 */
function addTimeParams(params, startHour, endHour) {
    if (startHour !== null && endHour !== null) {
        params.append('start_hour', startHour);
        params.append('end_hour', endHour);
    }
}

export async function fetchMapData(mapName, startDate, endDate, ssidFilter, tabletId, startHour, endHour) {
    const params = new URLSearchParams({ map: mapName, ssid_filter: ssidFilter });
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    if (tabletId) { // Adiciona o ID do tablet se ele existir
        params.append('tablet_id', tabletId);
    }
    
    // Adiciona os novos parâmetros de hora
    addTimeParams(params, startHour, endHour);

    const response = await fetch(`/api/map_data?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de dados do mapa: ${response.status}`);
    return await response.json();
}

export async function fetchCriticalPoints(mapName, startDate, endDate, ssidFilter, tabletId, startHour, endHour) {
    const params = new URLSearchParams({ map: mapName, ssid_filter: ssidFilter });
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    if (tabletId) { // Adiciona o ID do tablet se ele existir
        params.append('tablet_id', tabletId);
    }

    // Adiciona os novos parâmetros de hora
    addTimeParams(params, startHour, endHour);

    const response = await fetch(`/api/critical_points?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de pontos críticos: ${response.status}`);
    return await response.json();
}

export async function fetchKpis(mapName, startDate, endDate, ssidFilter, tabletId, startHour, endHour) {
    const params = new URLSearchParams({ map: mapName, ssid_filter: ssidFilter });
    if (startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    if (tabletId) { // Adiciona o ID do tablet se ele existir
        params.append('tablet_id', tabletId);
    }

    // Adiciona os novos parâmetros de hora
    addTimeParams(params, startHour, endHour);

    const response = await fetch(`/api/kpis?${params.toString()}`);
    if (!response.ok) throw new Error(`Falha na API de KPIs: ${response.status}`);
    return await response.json();
}