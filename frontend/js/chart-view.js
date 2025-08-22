let criticalChart = null;

export function drawCriticalChart(chartData, onBarClickCallback) {
    const ctx = document.getElementById('critical-points-chart').getContext('2d');
    if (criticalChart) {
        criticalChart.destroy();
    }
    
    criticalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets.map(dataset => ({ ...dataset, backgroundColor: 'rgba(255, 99, 132, 0.7)' }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const pointData = chartData.datasets[0].full_data[clickedIndex];
                    if (pointData && pointData.lat && pointData.lng && onBarClickCallback) {
                        onBarClickCallback(pointData.lat, pointData.lng);
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (context) => `Local (Grid ID): ${context[0].dataset.full_data[context[0].dataIndex].grid_id}`,
                        label: (context) => ` Medições Ruins: ${context.dataset.full_data[context.dataIndex].bad} (de ${context.dataset.full_data[context.dataIndex].total} no total)`
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Ranking dos Piores Locais' } },
                y: { beginAtZero: true, title: { display: true, text: 'Quantidade de Medições Ruins' } }
            }
        }
    });
}