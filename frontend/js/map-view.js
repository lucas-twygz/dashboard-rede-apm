console.log("Arquivo map-view.js carregado com sucesso!");
const patioView = { lat: -3.549806, lng: -38.811906, zoom: 17 };
const tmutView = { lat: -3.525506, lng: -38.797690, zoom: 16 };

let map;
let goodZonesLayer, attentionZonesLayer, criticalZonesLayer;
let tempMarker;

export function initMap() {
    map = L.map('map-container', {
        dragging: false, zoomControl: false, scrollWheelZoom: false, doubleClickZoom: false,
        boxZoom: false, keyboard: false, tap: false, touchZoom: false
    }).setView([patioView.lat, patioView.lng], patioView.zoom);

    const mapboxAccessToken = 'pk.eyJ1IjoibHVjYXNhcG10ZXJtaW5hbHMiLCJhIjoiY21lbXNkd25mMHcxMzJxb2FkdGZ4cDk0eCJ9.LLXruRNJ_E-JjraFHhbalQ';

    L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token={accessToken}', {
        attribution: '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 22,
        accessToken: mapboxAccessToken
    }).addTo(map);

    goodZonesLayer = L.layerGroup().addTo(map);
    attentionZonesLayer = L.layerGroup().addTo(map);
    criticalZonesLayer = L.layerGroup().addTo(map);
}

export function setMapView(mapName) {
    const view = mapName === 'patio' ? patioView : tmutView;
    map.setView([view.lat, view.lng], view.zoom);
}

export function focusOnPoint(lat, lng) {
    if (tempMarker) { map.removeLayer(tempMarker); }
    map.setView([lat, lng], 18);
    tempMarker = L.marker([lat, lng], {
        icon: L.divIcon({ className: 'pulsing-icon', iconSize: [20, 20] })
    }).addTo(map);
    setTimeout(() => { if (tempMarker) { map.removeLayer(tempMarker); } }, 5000);
}

export function drawMapData(data) {
    goodZonesLayer.clearLayers();
    attentionZonesLayer.clearLayers();
    criticalZonesLayer.clearLayers();

    const draw = (zoneData, defaultStyle, tooltipPrefix, layerGroup) => {
        if (!zoneData || zoneData.length === 0) return;

        L.geoJSON(zoneData, {
            pointToLayer: (feature, latlng) => {
                const props = feature.properties;
                return L.circle(latlng, {
                    radius: props.radius,
                    fillColor: defaultStyle.color,
                    color: defaultStyle.color,
                    weight: 1,
                    fillOpacity: props.opacity
                });
            },
            onEachFeature: (feature, layer) => {
                const props = feature.properties;
                let tooltipContent = `<b>${tooltipPrefix}</b><br>Medições Agrupadas: ${props.point_count}`;

                if (props.point_details && props.point_details.length > 0) {
                    tooltipContent += `<hr style="margin: 5px 0;">`;
                    props.point_details.forEach(detail => {
                        tooltipContent += `<span class="copy-id" title="Clique para copiar">${detail.id}</span>, ${detail.time}<br>`;
                    });
                }
                
                let tooltipCloseTimeout;

                // Nova lógica para abrir e fechar o tooltip com atraso
                layer.on('mouseover', function(e) {
                    // Limpa o temporizador se o mouse voltar para o marcador
                    clearTimeout(tooltipCloseTimeout);
                    
                    // Abre o tooltip se ainda não estiver aberto
                    if (!this.getTooltip() || !this.getTooltip().isOpen()) {
                        this.bindTooltip(tooltipContent, { interactive: true, offset: L.point(15, 0) }).openTooltip(e.latlng);
                        const tooltipEl = this.getTooltip()._container;

                        // Adiciona ouvintes para o tooltip
                        tooltipEl.addEventListener('mouseover', () => {
                            clearTimeout(tooltipCloseTimeout);
                        });

                        tooltipEl.addEventListener('mouseout', () => {
                            // Inicia o contador de tempo quando o mouse sai
                            console.time('Tempo de fechamento do tooltip');
                            tooltipCloseTimeout = setTimeout(() => {
                                this.closeTooltip();
                                console.timeEnd('Tempo de fechamento do tooltip');
                            }, 200); // Atraso de 200ms
                        });
                    }
                });

                layer.on('mouseout', function() {
                    // Inicia o temporizador ao sair do marcador
                    tooltipCloseTimeout = setTimeout(() => {
                        this.closeTooltip();
                    }, 200);
                });
            }
        }).addTo(layerGroup);
    };

    draw(data.good_zones, { color: 'lime' }, 'Zona de Rede Boa', goodZonesLayer);
    draw(data.attention_zones, { color: 'yellow' }, 'Zona de Rede Média', attentionZonesLayer);
    draw(data.critical_zones, { color: 'red' }, 'Zona de Rede Ruim', criticalZonesLayer);
}