import { fetchMapData, fetchCriticalPoints } from './api.js';
import { initMap, drawMapData, setMapView, focusOnPoint } from './map-view.js';
import { drawProblemChart } from './chart-view.js';

/**
 * Exibe uma mensagem de feedback na tela por um curto período.
 * @param {string} text - O texto a ser exibido (ex: "ID Copiado!").
 */
function showCopyFeedback(text) {
    const feedbackEl = document.createElement('div');
    feedbackEl.className = 'copy-feedback';
    feedbackEl.textContent = text;
    document.body.appendChild(feedbackEl);

    // Remove o elemento após 2.5 segundos
    setTimeout(() => {
        feedbackEl.remove();
    }, 2500);
}

document.addEventListener('DOMContentLoaded', async () => {
    const btnPatio = document.getElementById('btn-patio');
    const btnTmut = document.getElementById('btn-tmut');
    initMap();

    // Lógica de clique para copiar o ID
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

    async function updateDashboard(mapName) {
        try {
            const chartData = await fetchCriticalPoints(mapName);
            drawProblemChart(chartData, focusOnPoint);
        } catch (error) {
            console.error("Erro ao carregar dados do gráfico:", error);
        }
    }

    async function updateMap(mapName) {
        // LOG 1: Confirma que a função updateMap foi chamada
        console.log(`[main.js] Chamando updateMap para: ${mapName}`);
        try {
            const mapData = await fetchMapData(mapName);
            // LOG 2: Confirma que a requisição da API foi bem-sucedida
            console.log("[main.js] Dados do mapa recebidos da API:", mapData);
            drawMapData(mapData);
        } catch (error) {
            console.error("Erro ao carregar dados do mapa:", error);
        }
    }

    btnPatio.addEventListener('click', () => {
        setMapView('patio');
        updateDashboard('patio');
        updateMap('patio'); // Atualiza o mapa também
        btnPatio.classList.add('active');
        btnTmut.classList.remove('active');
    });

    btnTmut.addEventListener('click', () => {
        setMapView('tmut');
        updateDashboard('tmut');
        updateMap('tmut'); // Atualiza o mapa também
        btnTmut.classList.add('active');
        btnPatio.classList.remove('active');
    });

    // Carga inicial
    console.log("[main.js] Carga inicial do dashboard...");
    updateMap('patio');
    updateDashboard('patio');
});