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

    map.setView([patioView.lat, patioView.lng], patioView.zoom);

    goodZonesLayer = L.layerGroup().addTo(map);
    attentionZonesLayer = L.layerGroup().addTo(map);
    criticalZonesLayer = L.layerGroup().addTo(map);
}

export function setMapView(mapName) {
    const view = mapName === 'patio' ? patioView : tmutView;
    map.setView([view.lat, view.lng], view.zoom);
}

export function focusOnPoint(lat, lng) {
    // ... (código inalterado) ...
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
            // A opção 'style' para polígonos não é mais necessária, pois só temos pontos
            pointToLayer: (feature, latlng) => {
                const props = feature.properties;
                // Cria o círculo usando as propriedades enviadas pela API
                return L.circle(latlng, {
                    radius: props.radius, // Raio dinâmico
                    fillColor: defaultStyle.color,
                    color: defaultStyle.color,
                    weight: 1,
                    fillOpacity: props.opacity // Opacidade dinâmica
                });
            },
            onEachFeature: (feature, layer) => {
                layer.bindTooltip(`<b>${tooltipPrefix}</b><br>Medições Agrupadas: ${feature.properties.point_count}`);
            }
        }).addTo(layerGroup);
    };

    // As opções de cor agora são mais simples
    draw(data.good_zones, { color: 'lime' }, 'Zona de Rede Boa', goodZonesLayer);
    draw(data.attention_zones, { color: 'yellow' }, 'Zona de Rede Média', attentionZonesLayer);
    draw(data.critical_zones, { color: 'red' }, 'Zona de Rede Ruim', criticalZonesLayer);
}