// ai-analysis.js - Módulo para integração da análise de IA

/**
 * Função para chamar a API de análise de IA
 * @param {Object} mapData - Dados do mapa atual
 * @param {Object} context - Contexto da análise (período, dispositivo, etc.)
 * @returns {Promise<string>} - Resultado da análise da IA
 */
export async function analyzeWithAI(mapData, context) {
    const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            map_data: mapData,
            context: context
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro ao comunicar com a API de IA');
    }

    const result = await response.json();
    return result.analysis;
}

/**
 * Função para preparar os dados do mapa para análise
 * @param {Object} cachedMapData - Dados do mapa em cache
 * @returns {Object} - Dados estruturados para análise
 */
export function prepareMapDataForAnalysis(cachedMapData) {
    if (!cachedMapData) return {};

    return {
        critical_zones: cachedMapData.critical_zones || [],
        attention_zones: cachedMapData.attention_zones || [],
        good_zones: cachedMapData.good_zones || [],
        total_zones: (cachedMapData.critical_zones?.length || 0) + 
                    (cachedMapData.attention_zones?.length || 0) + 
                    (cachedMapData.good_zones?.length || 0)
    };
}

/**
 * Função para preparar o contexto da análise
 * @param {string} startDate - Data de início
 * @param {string} endDate - Data de fim
 * @param {string} tabletId - ID do tablet (se específico)
 * @param {string} ssidFilter - Filtro SSID atual
 * @param {string} currentMap - Mapa atual (patio/tmut)
 * @returns {Object} - Contexto estruturado
 */
export function prepareAnalysisContext(startDate, endDate, tabletId, ssidFilter, currentMap) {
    const formatDate = (dateString) => {
        if (!dateString) return 'Não especificado';
        const [year, month, day] = dateString.split('-');
        return `${day}/${month}/${year}`;
    };

    let periodo = 'Todos os dados disponíveis';
    if (startDate && endDate) {
        if (startDate === endDate) {
            periodo = `Dia ${formatDate(startDate)}`;
        } else {
            periodo = `${formatDate(startDate)} até ${formatDate(endDate)}`;
        }
    }

    const dispositivo = tabletId ? `Tablet: ${tabletId}` : 'Todos os Dispositivos';

    const ssidLabels = {
        'main_network': 'Rede Principal',
        'disconnected': 'Desconectados',
        'other_networks': 'Outras Redes',
        'all': 'Todas as Redes'
    };

    const mapLabels = {
        'patio': 'Pátio',
        'tmut': 'TMUT'
    };

    return {
        periodo,
        dispositivo,
        filtro_ssid: ssidLabels[ssidFilter] || ssidFilter,
        area: mapLabels[currentMap] || currentMap
    };
}

/**
 * Função para renderizar o resultado da análise com markdown básico
 * @param {string} analysisText - Texto da análise retornado pela IA
 * @returns {string} - HTML formatado
 */
export function renderAnalysisResult(analysisText) {
    if (!analysisText) return '';

    // Converter markdown básico para HTML
    let html = analysisText
        // Headers
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // Lista com bullets
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        // Texto em negrito
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Emojis e ícones (manter como estão)
        .replace(/💡/g, '💡')
        .replace(/🚀/g, '🚀')
        // Quebras de linha
        .replace(/\n/g, '<br>');

    // Envolver listas em <ul>
    html = html.replace(/(<li>.*?<\/li>)/gs, (match) => {
        return `<ul>${match}</ul>`;
    });

    // Limpar <ul> tags duplicadas
    html = html.replace(/<\/ul>\s*<br>\s*<ul>/g, '');

    return html;
}

/**
 * Função principal para executar a análise completa
 * @param {Object} params - Parâmetros da análise
 * @param {Object} params.cachedMapData - Dados do mapa
 * @param {string} params.startDate - Data início
 * @param {string} params.endDate - Data fim  
 * @param {string} params.tabletId - ID do tablet
 * @param {string} params.ssidFilter - Filtro SSID
 * @param {string} params.currentMap - Mapa atual
 * @returns {Promise<string>} - HTML da análise formatada
 */
export async function performFullAnalysis({
    cachedMapData,
    startDate,
    endDate,
    tabletId,
    ssidFilter,
    currentMap
}) {
    const mapData = prepareMapDataForAnalysis(cachedMapData);
    const context = prepareAnalysisContext(startDate, endDate, tabletId, ssidFilter, currentMap);
    
    const analysisResult = await analyzeWithAI(mapData, context);
    return renderAnalysisResult(analysisResult);
}