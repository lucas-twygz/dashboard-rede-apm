// ai-analysis.js - Módulo para integração da análise de IA (CORRIGIDO)

/**
 * Função para chamar a API de análise de IA
 * @param {Object} mapData - Dados do mapa atual
 * @param {Object} context - Contexto da análise (período, dispositivo, etc.)
 * @returns {Promise<string>} - Resultado da análise da IA
 */
export async function analyzeWithAI(mapData, context) {
    try {
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
            let errorMessage = 'Erro na comunicação com o servidor';
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // Se não conseguir parsear o JSON, usa a mensagem padrão
                errorMessage = `Erro HTTP ${response.status}: ${response.statusText}`;
            }
            
            throw new Error(errorMessage);
        }

        const result = await response.json();
        return result.analysis || 'Análise não disponível';
        
    } catch (error) {
        // Re-throw com mensagem mais amigável
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Não foi possível conectar ao servidor. Verifique sua conexão.');
        }
        throw error;
    }
}

/**
 * Função para preparar os dados do mapa para análise
 * @param {Object} cachedMapData - Dados do mapa em cache
 * @returns {Object} - Dados estruturados para análise
 */
export function prepareMapDataForAnalysis(cachedMapData) {
    if (!cachedMapData) {
        return {
            critical_zones: [],
            attention_zones: [],
            good_zones: [],
            total_zones: 0
        };
    }

    const criticalZones = cachedMapData.critical_zones || [];
    const attentionZones = cachedMapData.attention_zones || [];
    const goodZones = cachedMapData.good_zones || [];

    return {
        critical_zones: criticalZones,
        attention_zones: attentionZones,
        good_zones: goodZones,
        total_zones: criticalZones.length + attentionZones.length + goodZones.length
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
    // Função helper para formatar datas
    const formatDate = (dateString) => {
        if (!dateString) return 'Não especificado';
        try {
            const [year, month, day] = dateString.split('-');
            return `${day}/${month}/${year}`;
        } catch (error) {
            return 'Data inválida';
        }
    };

    // Determinar período
    let periodo = 'Todos os dados disponíveis';
    if (startDate && endDate) {
        if (startDate === endDate) {
            periodo = `Dia ${formatDate(startDate)}`;
        } else {
            periodo = `${formatDate(startDate)} até ${formatDate(endDate)}`;
        }
    } else if (startDate) {
        periodo = `A partir de ${formatDate(startDate)}`;
    } else if (endDate) {
        periodo = `Até ${formatDate(endDate)}`;
    }

    // Determinar dispositivo
    const dispositivo = (tabletId && tabletId.trim() !== '') 
        ? `Tablet: ${tabletId.trim()}` 
        : 'Todos os Dispositivos';

    // Labels para filtros SSID
    const ssidLabels = {
        'main_network': 'Rede Principal (2G_6qmzayp)',
        'disconnected': 'Dispositivos Desconectados',
        'other_networks': 'Outras Redes Wi-Fi',
        'all': 'Todas as Redes'
    };

    // Labels para mapas
    const mapLabels = {
        'patio': 'Área do Pátio',
        'tmut': 'Área TMUT'
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
    if (!analysisText || typeof analysisText !== 'string') {
        return '<p class="error-message">Análise não disponível.</p>';
    }

    try {
        // Converter markdown básico para HTML
        let html = analysisText
            // Headers (ordem importante: h3 antes de h2, h2 antes de h1)
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Texto em negrito
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Lista com bullets (preservar numeração)
            .replace(/^\d+\.\s+(.*$)/gim, '<li class="numbered">$1</li>')
            .replace(/^[-*]\s+(.*$)/gim, '<li>$1</li>')
            // Quebras de linha
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Envolver em parágrafo se não começar com tag HTML
        if (!html.startsWith('<')) {
            html = `<p>${html}</p>`;
        }

        // Processar listas
        html = html.replace(/(<li class="numbered">.*?<\/li>)/gs, (match) => {
            return `<ol>${match.replace(/class="numbered"/g, '')}</ol>`;
        });

        html = html.replace(/(<li>.*?<\/li>)/gs, (match) => {
            if (match.includes('<ol>')) return match;
            return `<ul>${match}</ul>`;
        });

        // Limpar tags duplicadas
        html = html.replace(/<\/ul>\s*<br>\s*<ul>/g, '');
        html = html.replace(/<\/ol>\s*<br>\s*<ol>/g, '');
        html = html.replace(/<\/p><p><\/p>/g, '</p>');

        return html;
        
    } catch (error) {
        console.error('Erro ao renderizar análise:', error);
        return `<p class="error-message">Erro ao formatar a análise: ${error.message}</p>`;
    }
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
    try {
        // Preparar dados
        const mapData = prepareMapDataForAnalysis(cachedMapData);
        const context = prepareAnalysisContext(startDate, endDate, tabletId, ssidFilter, currentMap);
        
        // Log para debug
        console.log('Dados preparados para análise:', { mapData, context });
        
        // Chamar API de análise
        const analysisResult = await analyzeWithAI(mapData, context);
        
        // Renderizar resultado
        return renderAnalysisResult(analysisResult);
        
    } catch (error) {
        console.error('Erro na análise completa:', error);
        
        // Retornar mensagem de erro formatada
        return `
            <div class="error-container" style="color: #d32f2f; padding: 15px; background-color: #ffebee; border-radius: 5px; border-left: 4px solid #d32f2f; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #d32f2f;">⚠️ Erro na Análise</h3>
                <p><strong>Detalhes:</strong> ${error.message}</p>
                <p><strong>Sugestões:</strong></p>
                <ul>
                    <li>Verifique sua conexão com a internet</li>
                    <li>Certifique-se de que os dados do mapa foram carregados</li>
                    <li>Tente novamente em alguns segundos</li>
                    <li>Se o problema persistir, entre em contato com o suporte</li>
                </ul>
            </div>
        `;
    }
}