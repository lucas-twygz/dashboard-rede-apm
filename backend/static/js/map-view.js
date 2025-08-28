const patioView = { lat: -3.549806, lng: -38.811906, zoom: 17 };
const tmutView = { lat: -3.525506, lng: -38.797690, zoom: 16 };

let map;
let goodZonesLayer, attentionZonesLayer, criticalZonesLayer;

// Referências para os elementos de controle de camada
const goodCountSpan = document.getElementById('good-count');
const attentionCountSpan = document.getElementById('attention-count');
const criticalCountSpan = document.getElementById('critical-count');

export function initMap() {
    map = L.map('map-container', {
        dragging: false,
        zoomControl: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        boxZoom: false,
        keyboard: false,
        tap: false,
        touchZoom: false
    }).setView([patioView.lat, patioView.lng], patioView.zoom);

    const mapboxAccessToken = 'pk.eyJ1IjoibHVjYXNhcG10ZXJtaW5hbHMiLCJhIjoiY21lbXNkd25mMHcxMzJxb2FkdGZ4cDk0eCJ9.LLXruRNJ_E-JjraFHhbalQ';
    L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token={accessToken}', {
        attribution: '© Mapbox © OpenStreetMap',
        maxZoom: 22,
        accessToken: mapboxAccessToken
    }).addTo(map);

    // Cria painéis para garantir a ordem correta de sobreposição (zIndex)
    map.createPane('goodPane').style.zIndex = 450;
    map.createPane('attentionPane').style.zIndex = 460;
    map.createPane('criticalPane').style.zIndex = 470;

    // Cria as camadas e já as adiciona ao mapa. A visibilidade será controlada pelo main.js
    goodZonesLayer = L.layerGroup().addTo(map);
    attentionZonesLayer = L.layerGroup().addTo(map);
    criticalZonesLayer = L.layerGroup().addTo(map);
}

export function setMapView(mapName) {
    const view = mapName === 'patio' ? patioView : tmutView;
    map.setView([view.lat, view.lng], view.zoom);
}

export function focusOnPoint(lat, lng) {
    map.setView([lat, lng], 18);
}

export function drawMapData(data) {
    // Limpa as camadas antes de redesenhar
    goodZonesLayer.clearLayers();
    attentionZonesLayer.clearLayers();
    criticalZonesLayer.clearLayers();

    // Atualiza os contadores de ocorrências
    goodCountSpan.textContent = data.good_zones.length;
    attentionCountSpan.textContent = data.attention_zones.length;
    criticalCountSpan.textContent = data.critical_zones.length;

    const draw = (zoneData, defaultStyle, tooltipPrefix, layerGroup, paneName) => {
        if (!zoneData || zoneData.length === 0) return;

        L.geoJSON(zoneData, {
            pane: paneName, // Associa a camada ao painel correto
            pointToLayer: (feature, latlng) => {
                return L.circle(latlng, {
                    radius: feature.properties.radius,
                    fillColor: defaultStyle.color,
                    color: defaultStyle.color,
                    weight: 1,
                    fillOpacity: feature.properties.opacity
                });
            },
            onEachFeature: (feature, layer) => {
                let popupContent = `<div class="popup-content"><b>${tooltipPrefix}</b><br>Medições Agrupadas: ${feature.properties.point_count}<hr style="margin: 5px 0;">`;
                if (feature.properties.point_details) {
                    feature.properties.point_details.forEach(detail => {
                        popupContent += `<div><span class="copy-id" title="Clique para copiar">${detail.id}</span>, ${detail.time}, <b>${detail.ssid}</b></div>`;
                    });
                }
                popupContent += `</div>`;
                layer.bindTooltip(`<b>${tooltipPrefix}</b><br>${feature.properties.point_count} medições agrupadas`);
                layer.bindPopup(popupContent);
            }
        }).addTo(layerGroup);
    };

    // Desenha cada camada no seu respectivo painel para garantir a ordem
    draw(data.good_zones, { color: 'lime' }, 'Zona de Rede Boa', goodZonesLayer, 'goodPane');
    draw(data.attention_zones, { color: 'yellow' }, 'Zona de Rede Média', attentionZonesLayer, 'attentionPane');
    draw(data.critical_zones, { color: 'red' }, 'Zona de Rede Ruim', criticalZonesLayer, 'criticalPane');
}