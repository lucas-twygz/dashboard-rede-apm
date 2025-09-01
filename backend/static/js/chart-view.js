let problemChart = null;

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
                label: 'Críticos',
                data: criticalData,
                backgroundColor: '#E61F25',
            }, {
                label: 'Atenção',
                data: attentionData,
                backgroundColor: '#FFC107',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const pointData = apiData[clickedIndex];
                    if (pointData && typeof pointData.lat !== 'undefined' && typeof pointData.lon !== 'undefined' && onBarClickCallback) {
                        onBarClickCallback(pointData.lat, pointData.lon);
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#f0f0f0',
                        font: {
                            family: 'Lato'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        title: (context) => `Local (Cluster ID): ${context[0].label}`,
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
                        text: 'Ranking dos Piores Locais',
                        color: '#f0f0f0',
                        font: {
                            family: 'Lato',
                            size: 14
                        }
                    },
                    ticks: {
                        color: '#f0f0f0',
                        font: {
                            family: 'Lato'
                        }
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Quantidade de Medições',
                        color: '#f0f0f0',
                        font: {
                            family: 'Lato',
                            size: 14
                        }
                    },
                    ticks: {
                        color: '#f0f0f0',
                        font: {
                            family: 'Lato'
                        }
                    }
                }
            }
        }
    });
}