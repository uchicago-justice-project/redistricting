// Interactive 2: Ward stability gradient map.
// Color encodes when a hexagon's ward last changed; hover shows full ward history.
// Address search via Nominatim (no API key required).

const HIST_YEARS = [1923, 1931, 1947, 1961, 1970, 1981, 1985, 1995, 2005, 2015, 2023];
const HIST_CHICAGO = { center: [-87.6298, 41.8781], zoom: 9 };

const historyMap = new maplibregl.Map({
  container: 'history-map',
  style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  center: HIST_CHICAGO.center,
  zoom: HIST_CHICAGO.zoom,
});

historyMap.addControl(new maplibregl.NavigationControl(), 'top-right');

const popup = new maplibregl.Popup({
  closeButton: false,
  closeOnClick: false,
  maxWidth: '260px',
});

let searchMarker = null;

historyMap.on('load', async () => {
  const [hexData, wardData] = await Promise.all([
    fetch('./data/chicago_hexagons_web.geojson').then(r => r.json()),
    fetch('./data/chicago_wards_all_years.geojson').then(r => r.json()),
  ]);

  historyMap.addSource('hexagons', { type: 'geojson', data: hexData });
  historyMap.addSource('ward-lines', { type: 'geojson', data: wardData });

  historyMap.addLayer({
    id: 'hex-fill',
    type: 'fill',
    source: 'hexagons',
    paint: {
      'fill-color': sinceYearColorExpr(),
      'fill-opacity': 0.5,
    },
  });

  historyMap.addLayer({
    id: 'hex-outline',
    type: 'line',
    source: 'hexagons',
    paint: {
      'line-color': 'rgba(255,255,255,0.1)',
      'line-width': 0.3,
    },
  });

  historyMap.addLayer({
    id: 'ward-lines',
    type: 'line',
    source: 'ward-lines',
    filter: ['==', ['get', 'year'], 2023],
    paint: {
      'line-color': '#cccccc',
      'line-width': 1,
    },
  });

  document.getElementById('ward-year-picker').addEventListener('change', e => {
    historyMap.setFilter('ward-lines', ['==', ['get', 'year'], Number(e.target.value)]);
  });

  if ('ontouchstart' in window) {
    historyMap.on('click', 'hex-fill', onHexHover);
    historyMap.on('click', onMapClick);
  } else {
    historyMap.on('mousemove', 'hex-fill', onHexHover);
    historyMap.on('mouseleave', 'hex-fill', onHexLeave);
  }

  initAddressSearch();
  hideLoading('history-loading');
});

// Discrete 5-category color scheme matching update_wards.py (viridis palette).
// Breaks: stable since 2015, 1995, 1975, 1947, 1923.
// since_year = 0 means the hexagon was never assigned a ward (not in city).
const SINCE_COLORS = {
  2015: '#b2e2dd',  // lightest teal — most recent change
  1995: '#66bdb6',
  1970: '#2a9d8f',
  1947: '#1a6b5e',
  1923: '#0d3b34',  // darkest teal — most stable
  none: '#cccccc',  // gray — not in city
};

function sinceYearColorExpr() {
  return [
    'case',
    ['==', ['get', 'since_year'], 0],     SINCE_COLORS.none,
    ['>=', ['get', 'since_year'], 2015],  SINCE_COLORS[2015],
    ['>=', ['get', 'since_year'], 1995],  SINCE_COLORS[1995],
    ['>=', ['get', 'since_year'], 1970],  SINCE_COLORS[1970],
    ['>=', ['get', 'since_year'], 1947],  SINCE_COLORS[1947],
    SINCE_COLORS[1923],
  ];
}

function onHexHover(e) {
  historyMap.getCanvas().style.cursor = 'pointer';
  const props = e.features[0].properties;
  popup.setLngLat(e.lngLat).setHTML(buildTooltip(props)).addTo(historyMap);
}

function onMapClick(e) {
  const features = historyMap.queryRenderedFeatures(e.point, { layers: ['hex-fill'] });
  if (!features.length) popup.remove();
}

function onHexLeave() {
  historyMap.getCanvas().style.cursor = '';
  popup.remove();
}

// Build tooltip HTML showing ward assignment per redistricting year.
function buildTooltip(props) {
  const notInCity1923 = props.ward1923 === 0 || props.ward1923 === '0';

  const header = notInCity1923
    ? '<strong>Not in city in 1923</strong>'
    : '<strong>Ward history</strong>';

  const rows = HIST_YEARS
    .filter(y => Number(props[`ward${y}`]) !== 0)
    .map(y => `<div class="ward-segment">${y}: <span>Ward ${Number(props[`ward${y}`])}</span></div>`)
    .join('');

  return `<div class="hex-tooltip">${header}${rows || '<div class="ward-segment">No ward data</div>'}</div>`;
}

// Address search using Nominatim (OpenStreetMap), no API key required.
function initAddressSearch() {
  document.getElementById('search-btn').addEventListener('click', geocode);
  document.getElementById('address-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') geocode();
  });
}

async function geocode() {
  const input = document.getElementById('address-input');
  const errorEl = document.getElementById('search-error');
  const query = input.value.trim();
  errorEl.textContent = '';

  if (!query) return;

  // Bias toward Chicago with a bounding box
  const chicagoBbox = '-88.0,41.6,-87.2,42.1';
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query + ', Chicago, IL')}&format=json&limit=1&countrycodes=us&bounded=1&viewbox=${chicagoBbox}`;

  try {
    const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
    const results = await res.json();

    if (!results.length) {
      errorEl.textContent = 'Address not found.';
      return;
    }

    const { lon, lat, display_name } = results[0];
    const lngLat = [parseFloat(lon), parseFloat(lat)];

    historyMap.flyTo({ center: lngLat, zoom: 15, duration: 900 });

    if (searchMarker) searchMarker.remove();
    searchMarker = new maplibregl.Marker({ color: '#e8521a' })
      .setLngLat(lngLat)
      .addTo(historyMap);
  } catch {
    errorEl.textContent = 'Search failed — please try again.';
  }
}

function hideLoading(id) {
  const el = document.getElementById(id);
  el.classList.add('hidden');
  setTimeout(() => el.remove(), 350);
}
