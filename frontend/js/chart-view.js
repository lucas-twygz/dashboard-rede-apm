let problemChart = null;

/**
 * Desenha ou atualiza o gráfico de barras empilhadas dos 10 piores locais.
 * @param {Array} apiData - Os dados da API (lista de locais com problemas).
 * @param {Function} onBarClickCallback - Função a ser chamada quando uma barra é clicada.
 */
export function drawProblemChart(apiData, onBarClickCallback) {
    const ctx = document.getElementById('critical-points-chart').getContext('2d');

    if (problemChart) {
        problemChart.destroy();
    }

    const labels = apiData.map(item => item.grid_id);
    const criticalData = apiData.map(item => item.critical_count);
    const attentionData = apiData.map(item => item.attention_count);

    problemChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Atenção',
                data: attentionData,
                backgroundColor: '#FFC107' ,
            }, {
                label: 'Críticos',
                data: criticalData,
                backgroundColor: '#E61F25',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const pointData = apiData[clickedIndex];
                    if (pointData && pointData.lat && pointData.lon && onBarClickCallback) {
                        onBarClickCallback(pointData.lat, pointData.lon);
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        title: (context) => `Local (Grid ID): ${context[0].label}`,
                        label: (context) => {
                            const item = apiData[context.dataIndex];
                            if (context.dataset.label === 'Críticos') {
                                return ` Críticos: ${item.critical_count}`;
                            }
                            if (context.dataset.label === 'Atenção') {
                                return ` Atenção: ${item.attention_count}`;
                            }
                            return '';
                        },
                        footer: (context) => {
                            const item = apiData[context[0].dataIndex];
                            return `Total de Problemas: ${item.total_problems}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Ranking dos Piores Locais'
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Quantidade de Medições'
                    }
                }
            }
        }
    });
}