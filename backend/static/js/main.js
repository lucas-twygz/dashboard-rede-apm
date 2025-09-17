import { fetchMapData, fetchCriticalPoints, fetchKpis } from './api.js';
import { initMap, drawMapData, setMapView, focusOnPoint } from './map-view.js';
import { drawProblemChart } from './chart-view.js';
import { performFullAnalysis } from './ai-analysis.js';

const AUTO_REFRESH_INTERVAL = 60000;

function showCopyFeedback(text) {
    const feedbackEl = document.createElement('div');
    feedbackEl.className = 'copy-feedback';
    feedbackEl.textContent = text;
    document.body.appendChild(feedbackEl);
    setTimeout(() => { feedbackEl.remove(); }, 2500);
}

async function copyTextToClipboard(text, successMessage) {
    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(text);
            showCopyFeedback(successMessage);
            return;
        } catch (err) {
            console.error('Falha ao copiar com a API moderna, tentando fallback:', err);
        }
    }

    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '-9999px';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopyFeedback(successMessage);
        } else {
            showCopyFeedback('Erro ao copiar');
        }
    } catch (err) {
        console.error('Falha ao copiar com o método de fallback:', err);
        showCopyFeedback('Erro ao copiar');
    }
    document.body.removeChild(textArea);
}

document.addEventListener('DOMContentLoaded', () => {
    const btnPatio = document.getElementById('btn-patio');
    const btnTmut = document.getElementById('btn-tmut');
    const btnDepot = document.getElementById('btn-depot');
    const btnResetFilter = document.getElementById('btn-reset-filter');
    const btnResetMap = document.getElementById('btn-reset-map');
    const dateStartInput = document.getElementById('date-start');
    const dateEndInput = document.getElementById('date-end');
    const ssidFilterRadios = document.querySelectorAll('input[name="ssid_filter"]');
    const chartCanvas = document.getElementById('critical-points-chart');
    const noChartDataMessage = document.getElementById('no-chart-data-message');
    const mapDateInfo = document.getElementById('map-date-info');
    const chartTitle = document.querySelector('#chart-container h2');
    const loadingOverlay = document.getElementById('loading-overlay');
    const btnExportExcel = document.getElementById('btn-export-excel');
    const kpiTotalMeasurements = document.getElementById('kpi-total-measurements');
    const kpiCriticalPercentage = document.getElementById('kpi-critical-percentage');
    const kpiDisconnections = document.getElementById('kpi-disconnections');
    const kpiWorstTablet = document.getElementById('kpi-worst-tablet');
    const deviceIdInput = document.getElementById('device-id-input');
    const btnSearchDevice = document.getElementById('btn-search-device');
    const btnClearDevice = document.getElementById('btn-clear-device');
    const filterStatusInfo = document.getElementById('filter-status-info');
    const toggleGoodLayer = document.getElementById('toggle-good-layer');
    const toggleAttentionLayer = document.getElementById('toggle-attention-layer');
    const toggleCriticalLayer = document.getElementById('toggle-critical-layer');
    
    const analyzeBtn = document.getElementById('analyze-btn');
    const aiSpinner = document.getElementById('ai-spinner');
    const aiBtnText = document.getElementById('ai-btn-text');
    const aiAnalysisResult = document.getElementById('ai-analysis-result');
    
    let currentMap = 'patio';
    let cachedMapData = null;
    let cachedChartData = null;

    initMap();

    const filterStyles = {
        'main_network': { title: 'Áreas Críticas - Rede Principal', className: 'title-main-network' },
        'disconnected': { title: 'Áreas Críticas - Desconectados', className: 'title-disconnected' },
        'other_networks': { title: 'Áreas Críticas - Outras Redes', className: 'title-other-networks' },
        'all': { title: 'Áreas Críticas - Todas as Medições', className: 'title-all' }
    };

    function setDefaultDateToYesterday() {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const year = yesterday.getFullYear();
        const month = String(yesterday.getMonth() + 1).padStart(2, '0');
        const day = String(yesterday.getDate()).padStart(2, '0');
        const yesterdayString = `${year}-${month}-${day}`;
        dateStartInput.value = yesterdayString;
        dateEndInput.value = yesterdayString;
    }

    async function runAIAnalysis() {
        if (!cachedMapData) {
            alert('Carregue os dados do mapa primeiro antes de analisar.');
            return;
        }
        const originalBtnText = aiBtnText.textContent;
        analyzeBtn.disabled = true;
        aiBtnText.textContent = 'Analisando...';
        aiSpinner.style.display = 'block';
        aiAnalysisResult.innerHTML = '<p class="placeholder-text">Aguarde, a IA está processando os dados...</p>';
        try {
            const analysisHTML = await performFullAnalysis({
                cachedMapData,
                startDate: dateStartInput.value,
                endDate: dateEndInput.value,
                tabletId: deviceIdInput.value.trim(),
                ssidFilter: document.querySelector('input[name="ssid_filter"]:checked').value,
                currentMap
            });
            aiAnalysisResult.innerHTML = analysisHTML;
        } catch (error) {
            console.error('Erro na análise de IA:', error);
            aiAnalysisResult.innerHTML = `<div style="color: #d32f2f; padding: 15px; background-color: #ffebee; border-radius: 5px; border-left: 4px solid #d32f2f;"><strong>Erro na Análise:</strong><br>${error.message || 'Não foi possível conectar com o serviço de IA. Tente novamente mais tarde.'}</div>`;
        } finally {
            analyzeBtn.disabled = false;
            aiBtnText.textContent = originalBtnText;
            aiSpinner.style.display = 'none';
        }
    }

    async function updateAllViews(isAutoRefresh = false) {
        if (!isAutoRefresh) loadingOverlay.classList.remove('hidden');
        const startDate = dateStartInput.value;
        const endDate = dateEndInput.value;
        const ssidFilter = document.querySelector('input[name="ssid_filter"]:checked').value;
        const tabletId = deviceIdInput.value.trim();
        updateStatusTexts(startDate, endDate, tabletId);
        try {
            const [kpiData, mapData, chartData] = await Promise.all([
                fetchKpis(currentMap, startDate, endDate, ssidFilter, tabletId),
                fetchMapData(currentMap, startDate, endDate, ssidFilter, tabletId),
                fetchCriticalPoints(currentMap, startDate, endDate, ssidFilter, tabletId)
            ]);
            cachedMapData = mapData;
            cachedChartData = chartData;
            updateKpis(kpiData);
            updateVisualizationsFromCache();
            if (!isAutoRefresh && aiAnalysisResult.innerHTML.includes('placeholder-text') === false) {
                aiAnalysisResult.innerHTML = '<p class="placeholder-text">Dados atualizados. Clique em "Analisar" para nova análise.</p>';
            }
        } catch (error) {
            console.error("Falha ao atualizar o dashboard:", error);
            mapDateInfo.textContent = 'Erro ao carregar dados. Tente novamente.';
            cachedMapData = null;
            cachedChartData = null;
        } finally {
            if (!isAutoRefresh) loadingOverlay.classList.add('hidden');
        }
    }
    
    function updateVisualizationsFromCache() {
        if (!cachedMapData || !cachedChartData) return;
        const filteredMapData = {
            good_zones: toggleGoodLayer.checked ? cachedMapData.good_zones : [],
            attention_zones: toggleAttentionLayer.checked ? cachedMapData.attention_zones : [],
            critical_zones: toggleCriticalLayer.checked ? cachedMapData.critical_zones : []
        };
        drawMapData(filteredMapData);
        let filteredChartData = cachedChartData.map(item => {
            const critical_count = toggleCriticalLayer.checked ? item.critical_count : 0;
            const attention_count = toggleAttentionLayer.checked ? item.attention_count : 0;
            return { ...item, critical_count, attention_count, total_problems: critical_count + attention_count };
        }).filter(item => item.total_problems > 0);
        if (filteredChartData.length > 0) {
            chartCanvas.style.display = 'block';
            noChartDataMessage.style.display = 'none';
            drawProblemChart(filteredChartData, focusOnPoint);
        } else {
            chartCanvas.style.display = 'none';
            noChartDataMessage.style.display = 'block';
        }
    }

    function updateKpis(kpiData) {
        kpiTotalMeasurements.textContent = kpiData.total_measurements;
        kpiCriticalPercentage.textContent = `${kpiData.critical_percentage}%`;
        kpiDisconnections.textContent = kpiData.disconnections;
        kpiWorstTablet.textContent = kpiData.worst_tablet;
    }
    
    function updateStatusTexts(startDate, endDate, tabletId) {
        const ssidFilter = document.querySelector('input[name="ssid_filter"]:checked').value;
        const style = filterStyles[ssidFilter];
        if (style) {
            chartTitle.textContent = style.title;
            chartTitle.className = '';
            chartTitle.classList.add(style.className);
        }
        if (tabletId) {
            filterStatusInfo.textContent = `Exibindo dados do tablet: ${tabletId}`;
        } else {
            filterStatusInfo.textContent = 'Exibindo dados de todos os tablets';
        }
        if (startDate && endDate) {
            const format = (dateString) => { const [year, month, day] = dateString.split('-'); return `${day}/${month}/${year}`; };
            mapDateInfo.textContent = `Exibindo dados de: ${format(startDate)} a ${format(endDate)}`;
        } else {
            mapDateInfo.textContent = 'Exibindo: Todos os dados disponíveis';
        }
    }
    
    document.body.addEventListener('click', (event) => {
        const copyElement = event.target.closest('.copy-id');
        if (copyElement) {
            const idToCopy = copyElement.textContent;
            if (idToCopy && idToCopy !== '-' && idToCopy !== 'N/A') {
                const message = copyElement.id === 'kpi-worst-tablet' ? 'ID do Tablet Copiado!' : 'ID Copiado!';
                copyTextToClipboard(idToCopy, message);
            }
        }

        const focusElement = event.target.closest('.focus-location');
        if (focusElement) {
            event.preventDefault(); 
            const lat = parseFloat(focusElement.dataset.lat);
            const lon = parseFloat(focusElement.dataset.lon);
            if (!isNaN(lat) && !isNaN(lon)) {
                focusOnPoint(lat, lon);
                const mapContainer = document.getElementById('map-container');
                if (mapContainer) {
                    mapContainer.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            } else {
                console.error('Coordenadas para foco são inválidas:', focusElement.dataset.lat, focusElement.dataset.lon);
            }
        }
    });

    // --- Event Listeners ---
    [toggleGoodLayer, toggleAttentionLayer, toggleCriticalLayer].forEach(el => el.addEventListener('change', updateVisualizationsFromCache));
    btnPatio.addEventListener('click', () => { 
        currentMap = 'patio'; 
        setMapView(currentMap); 
        updateAllViews(); 
        btnPatio.classList.add('active'); 
        btnTmut.classList.remove('active'); 
        btnDepot.classList.remove('active'); 
    });
    btnTmut.addEventListener('click', () => { 
        currentMap = 'tmut'; 
        setMapView(currentMap); 
        updateAllViews(); 
        btnTmut.classList.add('active'); 
        btnPatio.classList.remove('active'); 
        btnDepot.classList.remove('active'); 
    });
    btnDepot.addEventListener('click', () => { 
        currentMap = 'depot'; 
        setMapView(currentMap); 
        updateAllViews(); 
        btnDepot.classList.add('active'); 
        btnPatio.classList.remove('active'); 
        btnTmut.classList.remove('active'); 
    });
    btnResetFilter.addEventListener('click', () => { setDefaultDateToYesterday(); deviceIdInput.value = ''; updateAllViews(); });
    btnResetMap.addEventListener('click', () => setMapView(currentMap));
    ssidFilterRadios.forEach(radio => radio.addEventListener('change', () => updateAllViews()));
    
    // --- LINHA CORRIGIDA ---
    [dateStartInput, dateEndInput].forEach(el => el.addEventListener('change', () => updateAllViews()));
    
    btnSearchDevice.addEventListener('click', () => updateAllViews());
    deviceIdInput.addEventListener('keypress', (event) => { if (event.key === 'Enter') updateAllViews(); });
    btnClearDevice.addEventListener('click', () => { deviceIdInput.value = ''; updateAllViews(); });
    analyzeBtn.addEventListener('click', runAIAnalysis);
    
    btnExportExcel.addEventListener('click', async () => { 
        const startDate = dateStartInput.value;
        const endDate = dateEndInput.value;
        const ssidFilter = document.querySelector('input[name="ssid_filter"]:checked').value;
        const tabletId = deviceIdInput.value.trim();
        if (!startDate || !endDate) {
            alert('Por favor, selecione as datas de início e fim para exportar.');
            return;
        }
        try {
            loadingOverlay.classList.remove('hidden');
            const params = new URLSearchParams({
                start_date: startDate, end_date: endDate, ssid_filter: ssidFilter,
                ...(tabletId && { tablet_id: tabletId })
            });
            const response = await fetch(`/api/export?${params}`);
            if (!response.ok) {
                throw new Error(await response.text());
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Relatorio_WiFi_${startDate}_a_${endDate}.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erro na exportação:', error);
            alert('Erro ao exportar dados: ' + error.message);
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    });

    setDefaultDateToYesterday();
    updateAllViews();
    setInterval(() => {
        console.log("Atualizando dados automaticamente...");
        updateAllViews(true);
    }, AUTO_REFRESH_INTERVAL);
});