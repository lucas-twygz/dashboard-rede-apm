const patioView = { lat: -3.549806, lng: -38.811906, zoom: 17 };
const tmutView = { lat: -3.525506, lng: -38.797690, zoom: 16 };

let map;
let goodZonesLayer, attentionZonesLayer, criticalZonesLayer;

// Referências para os elementos de controle de camada
const toggleGoodLayer = document.getElementById('toggle-good-layer');
const toggleAttentionLayer = document.getElementById('toggle-attention-layer');
const toggleCriticalLayer = document.getElementById('toggle-critical-layer');
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

    // --- ALTERAÇÃO PRINCIPAL AQUI ---
    // A linha de código que contactava o Mapbox foi substituída.
    // Agora, o Leaflet irá procurar os "azulejos" do mapa na sua pasta local.
    const tileUrl = "/static/tiles/{z}/{x}/{y}.png";

    L.tileLayer(tileUrl, {
        attribution: 'APM Terminals Pecém', // Podemos colocar uma atribuição personalizada
        minZoom: 15, // Nível mínimo de zoom que baixámos
        maxZoom: 18  // Nível máximo de zoom que baixámos
    }).addTo(map);
    // --- FIM DA ALTERAÇÃO ---

    // Cria painéis para garantir a ordem correta de sobreposição (zIndex)
    map.createPane('goodPane').style.zIndex = 450;
    map.createPane('attentionPane').style.zIndex = 460;
    map.createPane('criticalPane').style.zIndex = 470;

    goodZonesLayer = L.layerGroup();
    attentionZonesLayer = L.layerGroup();
    criticalZonesLayer = L.layerGroup();

    if (toggleGoodLayer.checked) map.addLayer(goodZonesLayer);
    if (toggleAttentionLayer.checked) map.addLayer(attentionZonesLayer);
    if (toggleCriticalLayer.checked) map.addLayer(criticalZonesLayer);

    toggleGoodLayer.addEventListener('change', () => {
        map.hasLayer(goodZonesLayer) ? map.removeLayer(goodZonesLayer) : map.addLayer(goodZonesLayer);
    });
    toggleAttentionLayer.addEventListener('change', () => {
        map.hasLayer(attentionZonesLayer) ? map.removeLayer(attentionZonesLayer) : map.addLayer(attentionZonesLayer);
    });
    toggleCriticalLayer.addEventListener('change', () => {
        map.hasLayer(criticalZonesLayer) ? map.removeLayer(criticalZonesLayer) : map.addLayer(criticalZonesLayer);
    });
}

export function setMapView(mapName) {
    const view = mapName === 'patio' ? patioView : tmutView;
    map.setView([view.lat, view.lng], view.zoom);
}

export function focusOnPoint(lat, lng) {
    map.setView([lat, lng], 18);
}

export function drawMapData(data) {
    goodZonesLayer.clearLayers();
    attentionZonesLayer.clearLayers();
    criticalZonesLayer.clearLayers();

    goodCountSpan.textContent = data.good_zones.length;
    attentionCountSpan.textContent = data.attention_zones.length;
    criticalCountSpan.textContent = data.critical_zones.length;

    const draw = (zoneData, defaultStyle, tooltipPrefix, layerGroup, paneName) => {
        if (!zoneData || zoneData.length === 0) return;

        L.geoJSON(zoneData, {
            pane: paneName,
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

    draw(data.good_zones, { color: 'lime' }, 'Zona de Rede Boa', goodZonesLayer, 'goodPane');
    draw(data.attention_zones, { color: 'yellow' }, 'Zona de Rede Média', attentionZonesLayer, 'attentionPane');
    draw(data.critical_zones, { color: 'red' }, 'Zona de Rede Ruim', criticalZonesLayer, 'criticalPane');
}