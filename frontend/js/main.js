import { fetchMapData, fetchCriticalPoints } from './api.js';
import { initMap, drawMapData, setMapView, focusOnPoint } from './map-view.js';
import { drawCriticalChart } from './chart-view.js';

document.addEventListener('DOMContentLoaded', async () => {
    const btnPatio = document.getElementById('btn-patio');
    const btnTmut = document.getElementById('btn-tmut');
    initMap();

    async function updateDashboard(mapName) {
        try {
            const chartData = await fetchCriticalPoints(mapName);
            drawCriticalChart(chartData, focusOnPoint);
        } catch (error) {
            console.error("Erro ao carregar dados do gráfico:", error);
        }
    }

    btnPatio.addEventListener('click', () => {
        setMapView('patio');
        updateDashboard('patio');
        btnPatio.classList.add('active');
        btnTmut.classList.remove('active');
    });

    btnTmut.addEventListener('click', () => {
        setMapView('tmut');
        updateDashboard('tmut');
        btnTmut.classList.add('active');
        btnPatio.classList.remove('active');
    });

    try {
        const mapData = await fetchMapData();
        drawMapData(mapData);
    } catch (error) {
        console.error("Erro ao carregar dados do mapa:", error);
    }
    
    updateDashboard('patio');
});