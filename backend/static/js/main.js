import { fetchMapData, fetchCriticalPoints } from './api.js';
import { initMap, drawMapData, setMapView, focusOnPoint } from './map-view.js';
import { drawProblemChart } from './chart-view.js';

// --- NOVO: Constante para o intervalo de atualização automática (em milissegundos) ---
const AUTO_REFRESH_INTERVAL = 60000; // 60 segundos

function showCopyFeedback(text) {
    const feedbackEl = document.createElement('div');
    feedbackEl.className = 'copy-feedback';
    feedbackEl.textContent = text;
    document.body.appendChild(feedbackEl);
    setTimeout(() => { feedbackEl.remove(); }, 2500);
}

document.addEventListener('DOMContentLoaded', () => {
    // ... (referências aos elementos do DOM permanecem as mesmas)
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
    
    let currentMap = 'patio';
    let lastValidStartDate = '';
    let lastValidEndDate = '';

    initMap();

    const filterStyles = {
        'main_network': { title: 'Top 10 Pontos Críticos - Rede Principal', className: 'title-main-network' },
        'disconnected': { title: 'Top 10 Pontos Críticos - Desconectados', className: 'title-disconnected' },
        'other_networks': { title: 'Top 10 Pontos Críticos - Outras Redes', className: 'title-other-networks' },
        'all': { title: 'Top 10 Pontos Críticos - Todas as Medições', className: 'title-all' }
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
        // Durante o auto-refresh, não mostra o loading para ser mais sutil
        if (!isAutoRefresh) {
            loadingOverlay.classList.remove('hidden');
        }

        const startDate = dateStartInput.value;
        const endDate = dateEndInput.value;
        const ssidFilter = document.querySelector('input[name="ssid_filter"]:checked').value;

        const style = filterStyles[ssidFilter];
        if (style) {
            chartTitle.textContent = style.title;
            chartTitle.className = '';
            chartTitle.classList.add(style.className);
        }

        if (startDate && endDate && startDate > endDate) {
            mapDateInfo.textContent = 'Erro: Datas inválidas.';
            dateStartInput.classList.add('is-invalid');
            dateEndInput.classList.add('is-invalid');
            dateStartInput.value = lastValidStartDate;
            dateEndInput.value = lastValidEndDate;
            if (!isAutoRefresh) loadingOverlay.classList.add('hidden');
            return;
        }

        dateStartInput.classList.remove('is-invalid');
        dateEndInput.classList.remove('is-invalid');
        
        lastValidStartDate = startDate;
        lastValidEndDate = endDate;

        if (startDate && endDate) {
            const format = (dateString) => {
                const [year, month, day] = dateString.split('-');
                return `${day}/${month}/${year}`;
            };
            mapDateInfo.textContent = `Exibindo dados de: ${format(startDate)} a ${format(endDate)}`;
        } else {
            mapDateInfo.textContent = 'Exibindo: Todos os dados disponíveis';
        }

        try {
            await Promise.all([
                updateMap(currentMap, startDate, endDate, ssidFilter),
                updateDashboard(currentMap, startDate, endDate, ssidFilter)
            ]);
        } catch (error) {
            console.error("Falha ao atualizar o dashboard:", error);
            mapDateInfo.textContent = 'Erro ao carregar dados. Tente novamente.';
        } finally {
            if (!isAutoRefresh) {
                loadingOverlay.classList.add('hidden');
            }
        }
    }
    
    // ... (funções updateDashboard, updateMap e listeners de eventos permanecem os mesmos)
    async function updateDashboard(mapName, startDate, endDate, ssidFilter) {
        const chartData = await fetchCriticalPoints(mapName, startDate, endDate, ssidFilter);
        if (chartData && chartData.length > 0) {
            chartCanvas.style.display = 'block';
            noChartDataMessage.style.display = 'none';
            drawProblemChart(chartData, focusOnPoint);
        } else {
            chartCanvas.style.display = 'none';
            noChartDataMessage.style.display = 'block';
        }
    }
    async function updateMap(mapName, startDate, endDate, ssidFilter) {
        const mapData = await fetchMapData(mapName, startDate, endDate, ssidFilter);
        drawMapData(mapData);
    }
    document.body.addEventListener('click', (event) => {
        if (event.target.classList.contains('copy-id')) {
            const idToCopy = event.target.textContent;
            navigator.clipboard.writeText(idToCopy).then(() => showCopyFeedback('ID Copiado!')).catch(err => {
                console.error('Falha ao copiar ID:', err);
                showCopyFeedback('Erro ao copiar');
            });
        }
    });
    btnPatio.addEventListener('click', () => { currentMap = 'patio'; setMapView(currentMap); updateAllViews(); btnPatio.classList.add('active'); btnTmut.classList.remove('active'); });
    btnTmut.addEventListener('click', () => { currentMap = 'tmut'; setMapView(currentMap); updateAllViews(); btnTmut.classList.add('active'); btnPatio.classList.remove('active'); });
    btnResetFilter.addEventListener('click', () => { setDefaultDateToYesterday(); updateAllViews(); });
    btnResetMap.addEventListener('click', () => setMapView(currentMap));
    ssidFilterRadios.forEach(radio => radio.addEventListener('change', () => updateAllViews()));
    dateStartInput.addEventListener('change', () => updateAllViews());
    dateEndInput.addEventListener('change', () => updateAllViews());

    // --- INICIALIZAÇÃO ---
    setDefaultDateToYesterday();
    updateAllViews(); // Carrega os dados iniciais

    // --- NOVO: Inicia o polling para atualização automática ---
    setInterval(() => {
        console.log("Atualizando dados automaticamente...");
        updateAllViews(true); // O 'true' indica que é um auto-refresh
    }, AUTO_REFRESH_INTERVAL);
});