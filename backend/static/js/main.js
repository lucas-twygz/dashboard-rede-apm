import { fetchMapData, fetchCriticalPoints, fetchKpis } from './api.js';
import { initMap, drawMapData, setMapView, focusOnPoint } from './map-view.js';
import { drawProblemChart } from './chart-view.js';

const AUTO_REFRESH_INTERVAL = 60000;

let cachedMapData = null;
let cachedChartData = null;

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
            console.error('Falha ao copiar com a API moderna:', err);
        }
    }
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
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
    
    let currentMap = 'patio';
    let lastValidStartDate = '';
    let lastValidEndDate = '';

    initMap();

    const filterStyles = {
        'all': { title: 'Top 10 Pontos Críticos - Todas as Medições', className: 'title-all' },
        'main_network': { title: 'Top 10 Pontos Críticos - Rede Principal', className: 'title-main-network' },
        'disconnected': { title: 'Top 10 Pontos Críticos - Desconectados', className: 'title-disconnected' },
        'other_networks': { title: 'Top 10 Pontos Críticos - Outras Redes', className: 'title-other-networks' }
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
        lastValidStartDate = yesterdayString;
        lastValidEndDate = yesterdayString;
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

        drawMapData(cachedMapData);

        let filteredChartData = cachedChartData;
        if (!toggleCriticalLayer.checked) {
            filteredChartData = filteredChartData.map(item => ({ ...item, critical_count: 0 }));
        }
        if (!toggleAttentionLayer.checked) {
            filteredChartData = filteredChartData.map(item => ({ ...item, attention_count: 0 }));
        }
        filteredChartData = filteredChartData.map(item => ({ ...item, total_problems: item.critical_count + item.attention_count }))
            .filter(item => item.total_problems > 0);

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
    });

    toggleGoodLayer.addEventListener('change', updateVisualizationsFromCache);
    toggleAttentionLayer.addEventListener('change', updateVisualizationsFromCache);
    toggleCriticalLayer.addEventListener('change', updateVisualizationsFromCache);

    btnPatio.addEventListener('click', () => { currentMap = 'patio'; setMapView(currentMap); updateAllViews(); btnPatio.classList.add('active'); btnTmut.classList.remove('active'); });
    btnTmut.addEventListener('click', () => { currentMap = 'tmut'; setMapView(currentMap); updateAllViews(); btnTmut.classList.add('active'); btnPatio.classList.remove('active'); });
    btnResetFilter.addEventListener('click', () => { setDefaultDateToYesterday(); deviceIdInput.value = ''; updateAllViews(); });
    btnResetMap.addEventListener('click', () => setMapView(currentMap));
    ssidFilterRadios.forEach(radio => radio.addEventListener('change', () => updateAllViews()));
    dateStartInput.addEventListener('change', () => updateAllViews());
    dateEndInput.addEventListener('change', () => updateAllViews());
    btnSearchDevice.addEventListener('click', () => updateAllViews());
    deviceIdInput.addEventListener('keypress', (event) => { if (event.key === 'Enter') updateAllViews(); });
    btnClearDevice.addEventListener('click', () => { deviceIdInput.value = ''; updateAllViews(); });
    btnExportExcel.addEventListener('click', async () => {
        const startDate = dateStartInput.value;
        const endDate = dateEndInput.value;
        const ssidFilter = document.querySelector('input[name="ssid_filter"]:checked').value;
        const tabletId = deviceIdInput.value.trim();

        if (!startDate || !endDate) {
            alert("Por favor, selecione as datas de início e fim para exportar.");
            return;
        }
        if (startDate > endDate) {
            alert("A data de início não pode ser maior que a data de fim.");
            return;
        }

        loadingOverlay.classList.remove('hidden');
        
        try {
            const params = new URLSearchParams({
                start_date: startDate,
                end_date: endDate,
                ssid_filter: ssidFilter
            });
            if (tabletId) {
                params.append('tablet_id', tabletId);
            }
            const exportUrl = `/api/export?${params.toString()}`;
            const response = await fetch(exportUrl);
            
            if (!response.ok) {
                const errorMessage = await response.text();
                alert(errorMessage);
                return;
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            const disposition = response.headers.get('Content-Disposition');
            let filename = `Relatorio_WiFi_${startDate}_a_${endDate}.xlsx`;
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disdisposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            console.error('Erro ao exportar arquivo:', error);
            alert('Ocorreu um erro inesperado ao tentar exportar o arquivo.');
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