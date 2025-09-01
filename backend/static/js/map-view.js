// Configurações de visualização para as áreas
const patioView = { center: [-38.811906, -3.549906], zoom: 16, bearing: 52, pitch: 0 };
const tmutView = { center: [-38.797690, -3.525506], zoom: 15.5, bearing: 50, pitch: 0 };

let map;
const toggleGoodLayer = document.getElementById('toggle-good-layer');
const toggleAttentionLayer = document.getElementById('toggle-attention-layer');
const toggleCriticalLayer = document.getElementById('toggle-critical-layer');
const goodCountSpan = document.getElementById('good-count');
const attentionCountSpan = document.getElementById('attention-count');
const criticalCountSpan = document.getElementById('critical-count');

const layerIds = ['good-zones-layer', 'attention-zones-layer', 'critical-zones-layer'];
const sourceIds = ['good-zones', 'attention-zones', 'critical-zones'];

export function initMap() {
    map = new maplibregl.Map({
        container: 'map-container',
        style: {
            version: 8,
            sources: {
                'raster-tiles': {
                    type: 'raster',
                    tiles: ['/static/tiles/{z}/{x}/{y}.png'],
                    tileSize: 256,
                    attribution: 'APM Terminals Pecém',
                    maxzoom: 18 
                }
            },
            layers: [{
                id: 'simple-tiles',
                type: 'raster',
                source: 'raster-tiles',
                minzoom: 15
            }]
        },
        center: patioView.center,
        zoom: patioView.zoom,
        bearing: patioView.bearing,
        pitch: patioView.pitch,
        dragPan: false,
        dragRotate: false,
        scrollZoom: false,
        touchZoomRotate: false,
        doubleClickZoom: false,
        attributionControl: false
    });

    toggleGoodLayer.addEventListener('change', () => toggleLayerVisibility('good-zones-layer', toggleGoodLayer.checked));
    toggleAttentionLayer.addEventListener('change', () => toggleLayerVisibility('attention-zones-layer', toggleAttentionLayer.checked));
    toggleCriticalLayer.addEventListener('change', () => toggleLayerVisibility('critical-zones-layer', toggleCriticalLayer.checked));
}

function toggleLayerVisibility(layerId, isVisible) {
    if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', isVisible ? 'visible' : 'none');
    }
}

export function setMapView(mapName) {
    const view = mapName === 'patio' ? patioView : tmutView;
    map.jumpTo({ ...view });
}

export function focusOnPoint(lat, lng) {
    map.flyTo({
        center: [lng, lat],
        zoom: 18,
        bearing: map.getBearing(),
        duration: 1500,
        essential: true
    });
}

export function drawMapData(data) {
    return new Promise(resolve => {
        goodCountSpan.textContent = data.good_zones.length;
        attentionCountSpan.textContent = data.attention_zones.length;
        criticalCountSpan.textContent = data.critical_zones.length;

        const prepareData = (zones) => ({
            type: 'FeatureCollection',
            features: zones.map(z => ({...z, properties: {...z.properties, point_details: JSON.stringify(z.properties.point_details)}}))
        });

        const render = () => {
            for (let i = 0; i < layerIds.length; i++) {
                if (map.getLayer(layerIds[i])) map.removeLayer(layerIds[i]);
                if (map.getSource(sourceIds[i])) map.removeSource(sourceIds[i]);
            }
            
            addSourceAndLayer('good-zones', 'good-zones-layer', prepareData(data.good_zones), 'lime');
            addSourceAndLayer('attention-zones', 'attention-zones-layer', prepareData(data.attention_zones), 'yellow');
            addSourceAndLayer('critical-zones', 'critical-zones-layer', prepareData(data.critical_zones), 'red');
            
            resolve();
        };

        const addSourceAndLayer = (sourceId, layerId, geojsonData, color) => {
            map.addSource(sourceId, { type: 'geojson', data: geojsonData });
            map.addLayer({
                id: layerId,
                type: 'circle',
                source: sourceId,
                paint: {
                    'circle-radius': ['get', 'radius'],
                    'circle-color': color,
                    'circle-opacity': ['get', 'opacity'],
                    'circle-stroke-width': 1,
                    'circle-stroke-color': color
                }
            });
            
            const checkbox = document.getElementById(`toggle-${layerId.split('-')[0]}-layer`);
            if (checkbox) {
                toggleLayerVisibility(layerId, checkbox.checked);
            }

            map.on('click', layerId, (e) => {
                const properties = e.features[0].properties;
                const details = JSON.parse(properties.point_details);
                let popupContent = `<div class="popup-content"><b>${properties.status === 'good' ? 'Zona de Rede Boa' : (properties.status === 'attention' ? 'Zona de Rede Média' : 'Zona de Rede Ruim')}</b><br>Medições Agrupadas: ${properties.point_count}<hr style="margin: 5px 0;">`;
                if (details) {
                    details.forEach(detail => {
                        popupContent += `<div><span class="copy-id" title="Clique para copiar">${detail.id}</span>, ${detail.time}, <b>${detail.ssid}</b></div>`;
                    });
                }
                popupContent += `</div>`;
                new maplibregl.Popup().setLngLat(e.lngLat).setHTML(popupContent).addTo(map);
            });
            map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer'; });
            map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = ''; });
        };

        if (map.isStyleLoaded() && !map.isMoving()) {
            render();
        } else {
            map.once('idle', render);
        }
    });
}