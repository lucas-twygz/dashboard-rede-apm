import { fetchMapData, fetchCriticalPoints } from './api.js';
import { initMap, drawMapData, setMapView, focusOnPoint } from './map-view.js';
import { drawProblemChart } from './chart-view.js';

function showCopyFeedback(text) {
    const feedbackEl = document.createElement('div');
    feedbackEl.className = 'copy-feedback';
    feedbackEl.textContent = text;
    document.body.appendChild(feedbackEl);

    setTimeout(() => {
        feedbackEl.remove();
    }, 2500);
}

document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos do DOM
    const btnPatio = document.getElementById('btn-patio');
    const btnTmut = document.getElementById('btn-tmut');
    const btnResetFilter = document.getElementById('btn-reset-filter');
    const btnResetMap = document.getElementById('btn-reset-map');
    const dateStartInput = document.getElementById('date-start');
    const dateEndInput = document.getElementById('date-end');
    const chartCanvas = document.getElementById('critical-points-chart');
    const noChartDataMessage = document.getElementById('no-chart-data-message');
    const mapDateInfo = document.getElementById('map-date-info');
    
    let currentMap = 'patio';
    let lastValidStartDate = '';
    let lastValidEndDate = '';

    initMap();

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

    async function updateAllViews() {
        const startDate = dateStartInput.value;
        const endDate = dateEndInput.value;

        if (startDate && endDate && startDate > endDate) {
            mapDateInfo.textContent = 'Erro: Datas inválidas.';
            dateStartInput.classList.add('is-invalid');
            dateEndInput.classList.add('is-invalid');
            dateStartInput.value = lastValidStartDate;
            dateEndInput.value = lastValidEndDate;
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
                updateMap(currentMap, startDate, endDate),
                updateDashboard(currentMap, startDate, endDate)
            ]);
        } catch (error) {
            console.error("Falha ao atualizar o dashboard:", error);
        }
    }

    async function updateDashboard(mapName, startDate, endDate) {
        const chartData = await fetchCriticalPoints(mapName, startDate, endDate);
        
        if (chartData && chartData.length > 0) {
            chartCanvas.style.display = 'block';
            noChartDataMessage.style.display = 'none';
            drawProblemChart(chartData, focusOnPoint);
        } else {
            chartCanvas.style.display = 'none';
            noChartDataMessage.style.display = 'block';
        }
    }
    
    async function updateMap(mapName, startDate, endDate) {
        const mapData = await fetchMapData(mapName, startDate, endDate);
        drawMapData(mapData);
    }

    document.body.addEventListener('click', (event) => {
        if (event.target.classList.contains('copy-id')) {
            const idToCopy = event.target.textContent;
            navigator.clipboard.writeText(idToCopy).then(() => {
                showCopyFeedback('ID Copiado!');
            }).catch(err => {
                console.error('Falha ao copiar ID:', err);
                showCopyFeedback('Erro ao copiar');
            });
        }
    });

    btnPatio.addEventListener('click', () => {
        currentMap = 'patio';
        setMapView(currentMap);
        updateAllViews();
        btnPatio.classList.add('active');
        btnTmut.classList.remove('active');
    });

    btnTmut.addEventListener('click', () => {
        currentMap = 'tmut';
        setMapView(currentMap);
        updateAllViews();
        btnTmut.classList.add('active');
        btnPatio.classList.remove('active');
    });

    btnResetFilter.addEventListener('click', () => {
        setDefaultDateToYesterday();
        updateAllViews();
    });

    btnResetMap.addEventListener('click', () => {
        setMapView(currentMap);
    });



    dateStartInput.addEventListener('change', updateAllViews);
    dateEndInput.addEventListener('change', updateAllViews);

    setDefaultDateToYesterday();
    updateAllViews();
});