// Build script to generate the interactive corridor map HTML
// Reads the JSON data files and embeds them into a self-contained HTML file

const fs = require('fs');
const path = require('path');

const baseDir = path.dirname(__filename);
const communitiesData = JSON.parse(fs.readFileSync(path.join(baseDir, 'communities_geo.json'), 'utf8'));
const corridorData = JSON.parse(fs.readFileSync(path.join(baseDir, 'corridor_polygon.json'), 'utf8'));
const inatData = JSON.parse(fs.readFileSync(path.join(baseDir, 'inaturalist_data.json'), 'utf8'));

// Build community table data
const communityTable = communitiesData.map(c => ({
  id: c.id,
  name: c.name,
  ha: c.ha
}));

// Build GeoJSON for communities
const communitiesGeoJSON = {
  type: "FeatureCollection",
  features: communitiesData.map(c => ({
    type: "Feature",
    properties: {
      id: c.id,
      name: c.name,
      ha: c.ha,
      centroid: c.centroid
    },
    geometry: {
      type: "Polygon",
      coordinates: c.rings.map(ring => ring.map(coord => [coord[0], coord[1]]))
    }
  }))
};

// Build GeoJSON for corridor
const corridorGeoJSON = {
  type: "Feature",
  properties: { name: "Corredor de Conectividad" },
  geometry: {
    type: "Polygon",
    coordinates: corridorData.rings.map(ring => ring.map(coord => [coord[0], coord[1]]))
  }
};

// Build species data per community (top 15 for popup display)
const communitySpecies = {};
for (const [id, data] of Object.entries(inatData.community_species)) {
  communitySpecies[id] = {
    name: data.name,
    total: data.total,
    species: (data.all_species || []).slice(0, 15).map(s => ({
      name: s.name,
      common_name: s.common_name || '',
      iconic_group: s.iconic_group,
      count: s.count,
      photo_url: s.photo_url
    }))
  };
}

// Color palette - warm earth tones matching reference image
const colors = [
  '#8B4513', '#A0522D', '#CD853F', '#D2691E', '#B8860B',
  '#DAA520', '#BC8F8F', '#F4A460', '#DEB887', '#D2B48C',
  '#C19A6B', '#8B6914', '#A52A2A', '#CD5C5C', '#E9967A',
  '#FA8072', '#FFA07A', '#FF7F50', '#FF6347', '#CC5500',
  '#B22222', '#DC143C', '#C0392B', '#E74C3C', '#922B21'
];

const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Corredor de Conectividad Comunitaria - Colonso-Sumaco-Galeras</title>
<meta name="description" content="Mapa interactivo del Corredor de Conectividad Comunitaria, Herencia Ancestral y Bioeconomía Colonso-Sumaco-Galeras. 25 comunidades con datos de biodiversidad de iNaturalist.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"><\/script>
<style>
  :root {
    --bg-primary: #0a0f1a;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.85);
    --bg-glass: rgba(17, 24, 39, 0.7);
    --border-glass: rgba(255, 255, 255, 0.08);
    --text-primary: #f0f0f0;
    --text-secondary: #9ca3af;
    --text-accent: #f59e0b;
    --accent-gold: #f59e0b;
    --accent-amber: #d97706;
    --accent-warm: #b45309;
    --gradient-title: linear-gradient(135deg, #f59e0b, #d97706, #b45309, #92400e);
    --gradient-card: linear-gradient(145deg, rgba(17,24,39,0.9), rgba(30,41,59,0.7));
    --shadow-glow: 0 0 30px rgba(245,158,11,0.15);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }

  /* === MAIN LAYOUT === */
  .app-container {
    display: grid;
    grid-template-rows: auto 1fr auto;
    grid-template-columns: 320px 1fr;
    height: 100vh;
    width: 100vw;
    gap: 0;
  }

  /* === TITLE BAR === */
  .title-bar {
    grid-column: 1 / -1;
    background: linear-gradient(135deg, #1a1005 0%, #2d1a0a 30%, #1a1005 100%);
    border-bottom: 2px solid rgba(245, 158, 11, 0.3);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    z-index: 100;
  }

  .title-bar::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(245,158,11,0.05), transparent);
    animation: shimmer 8s infinite;
  }

  @keyframes shimmer {
    0%, 100% { transform: translateX(-100%); }
    50% { transform: translateX(100%); }
  }

  .title-bar h1 {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    font-weight: 900;
    text-align: center;
    background: var(--gradient-title);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 2px;
    text-transform: uppercase;
    line-height: 1.3;
    text-shadow: none;
    position: relative;
    z-index: 1;
  }

  /* === LEFT PANEL === */
  .left-panel {
    background: var(--gradient-card);
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--border-glass);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0;
    z-index: 50;
  }

  .left-panel::-webkit-scrollbar { width: 4px; }
  .left-panel::-webkit-scrollbar-track { background: transparent; }
  .left-panel::-webkit-scrollbar-thumb { background: rgba(245,158,11,0.3); border-radius: 2px; }

  .panel-section {
    padding: 16px;
    border-bottom: 1px solid var(--border-glass);
  }

  .panel-section h3 {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--accent-gold);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .panel-section h3::before {
    content: '';
    width: 3px;
    height: 14px;
    background: var(--gradient-title);
    border-radius: 2px;
  }

  /* Inset Maps */
  .inset-map-container {
    width: 100%;
    height: 140px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border-glass);
    margin-bottom: 10px;
    position: relative;
  }

  .inset-map-container .inset-label {
    position: absolute;
    bottom: 4px;
    left: 4px;
    background: rgba(0,0,0,0.7);
    color: #fff;
    font-size: 0.6rem;
    padding: 2px 6px;
    border-radius: 3px;
    z-index: 1000;
    pointer-events: none;
  }

  /* Legend */
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-size: 0.72rem;
    color: var(--text-secondary);
  }

  .legend-color {
    width: 18px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.15);
    flex-shrink: 0;
  }

  .legend-line {
    width: 18px;
    height: 3px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .legend-dashed {
    width: 18px;
    height: 0;
    border-top: 2px dashed;
    flex-shrink: 0;
  }

  /* Info Section */
  .info-block {
    font-size: 0.68rem;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 6px;
  }

  .info-block strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  /* Logos Section */
  .logos-section {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: auto;
  }

  .logo-placeholder {
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border-glass);
    border-radius: 6px;
    padding: 8px 12px;
    text-align: center;
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--accent-gold);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .logos-row {
    display: flex;
    gap: 6px;
    align-items: stretch;
  }

  .logos-row .logo-placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 40px;
    font-size: 0.55rem;
  }

  /* === MAP AREA === */
  .map-area {
    position: relative;
    display: flex;
    flex-direction: column;
  }

  #map {
    flex: 1;
    z-index: 1;
  }

  .leaflet-container {
    background: #0a0f1a;
    font-family: 'Inter', sans-serif;
  }

  /* Custom Community Labels */
  .community-label {
    background: rgba(0, 0, 0, 0.75);
    border: 1px solid rgba(245, 158, 11, 0.5);
    border-radius: 50%;
    color: #f59e0b;
    font-size: 11px;
    font-weight: 800;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    pointer-events: none;
  }

  /* Park Label */
  .park-label {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    font-size: 16px;
    font-weight: 700;
    font-family: 'Playfair Display', serif;
    text-shadow: 2px 2px 6px rgba(0,0,0,0.9), -1px -1px 3px rgba(0,0,0,0.7);
    white-space: nowrap;
    pointer-events: none;
    letter-spacing: 2px;
  }

  /* Custom Popup Styles */
  .leaflet-popup-content-wrapper {
    background: rgba(10, 15, 26, 0.96);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6), var(--shadow-glow);
    color: var(--text-primary);
    padding: 0;
  }

  .leaflet-popup-content {
    margin: 0;
    width: 420px !important;
    max-height: 480px;
    overflow-y: auto;
    font-family: 'Inter', sans-serif;
  }

  .leaflet-popup-content::-webkit-scrollbar { width: 4px; }
  .leaflet-popup-content::-webkit-scrollbar-track { background: transparent; }
  .leaflet-popup-content::-webkit-scrollbar-thumb { background: rgba(245,158,11,0.3); border-radius: 2px; }

  .leaflet-popup-tip {
    background: rgba(10, 15, 26, 0.96);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  .leaflet-popup-close-button {
    color: var(--accent-gold) !important;
    font-size: 20px !important;
    width: 28px !important;
    height: 28px !important;
    line-height: 28px !important;
    top: 8px !important;
    right: 8px !important;
  }

  .popup-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-glass);
    background: linear-gradient(135deg, rgba(245,158,11,0.1), transparent);
  }

  .popup-header h2 {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--accent-gold);
    margin-bottom: 4px;
  }

  .popup-header .popup-meta {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .popup-header .popup-meta span {
    color: var(--text-primary);
    font-weight: 600;
  }

  .popup-species-title {
    padding: 10px 20px 6px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent-gold);
  }

  .species-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    padding: 8px 16px 16px;
  }

  .species-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .species-card:hover {
    border-color: rgba(245,158,11,0.4);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }

  .species-card img {
    width: 100%;
    height: 85px;
    object-fit: cover;
    display: block;
    background: rgba(255,255,255,0.03);
  }

  .species-card .species-info {
    padding: 6px 8px;
  }

  .species-card .species-name {
    font-size: 0.6rem;
    font-style: italic;
    color: var(--text-primary);
    line-height: 1.2;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .species-card .species-common {
    font-size: 0.55rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .species-card .species-group {
    display: inline-block;
    font-size: 0.5rem;
    padding: 1px 5px;
    border-radius: 3px;
    margin-top: 3px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .group-aves { background: rgba(59,130,246,0.2); color: #60a5fa; }
  .group-mammalia { background: rgba(239,68,68,0.2); color: #f87171; }
  .group-reptilia { background: rgba(16,185,129,0.2); color: #34d399; }
  .group-amphibia { background: rgba(168,85,247,0.2); color: #a78bfa; }
  .group-insecta { background: rgba(245,158,11,0.2); color: #fbbf24; }
  .group-plantae { background: rgba(34,197,94,0.2); color: #4ade80; }
  .group-mollusca { background: rgba(236,72,153,0.2); color: #f472b6; }
  .group-default { background: rgba(148,163,184,0.2); color: #94a3b8; }

  /* === BOTTOM TABLE === */
  .bottom-bar {
    grid-column: 1 / -1;
    background: linear-gradient(180deg, rgba(17,24,39,0.95), rgba(10,15,26,0.98));
    border-top: 1px solid var(--border-glass);
    padding: 10px 20px;
    overflow-x: auto;
    max-height: 180px;
    z-index: 50;
  }

  .bottom-bar h3 {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--accent-gold);
    margin-bottom: 8px;
  }

  .data-table-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.68rem;
  }

  .data-table th {
    background: rgba(245,158,11,0.1);
    color: var(--accent-gold);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.6rem;
    padding: 5px 8px;
    text-align: left;
    border-bottom: 1px solid rgba(245,158,11,0.2);
    position: sticky;
    top: 0;
  }

  .data-table td {
    padding: 4px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: var(--text-secondary);
  }

  .data-table td:first-child {
    color: var(--accent-gold);
    font-weight: 700;
    text-align: center;
    width: 30px;
  }

  .data-table td:last-child {
    text-align: right;
    font-family: 'Inter', sans-serif;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
    font-weight: 500;
  }

  .data-table tr:hover td {
    background: rgba(245,158,11,0.05);
  }

  .data-table tr {
    cursor: pointer;
    transition: background 0.15s;
  }

  /* Scale Bar */
  .leaflet-control-scale-line {
    background: rgba(10,15,26,0.8) !important;
    border-color: rgba(245,158,11,0.5) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
  }

  /* Custom attribution */
  .leaflet-control-attribution {
    background: rgba(10,15,26,0.8) !important;
    color: var(--text-secondary) !important;
    font-size: 0.55rem !important;
  }

  .leaflet-control-attribution a {
    color: var(--accent-gold) !important;
  }

  /* No species message */
  .no-species {
    padding: 20px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }

  /* === PRINT STYLES FOR A0 === */
  @media print {
    @page {
      size: 1189mm 841mm landscape;
      margin: 15mm;
    }

    body {
      overflow: visible;
      height: auto;
      width: auto;
      background: white;
      color: #1a1a1a;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    .app-container {
      height: auto;
      width: 100%;
      grid-template-rows: auto auto auto;
    }

    .title-bar {
      background: linear-gradient(135deg, #f5e6d0, #e8d5b5) !important;
      -webkit-print-color-adjust: exact;
    }

    .title-bar h1 {
      color: #3d1f00 !important;
      -webkit-text-fill-color: #3d1f00 !important;
      font-size: 2.5rem;
    }

    .left-panel {
      background: #f8f6f2 !important;
      border-right: 2px solid #d4c4a8 !important;
    }

    .bottom-bar {
      background: #f8f6f2 !important;
      border-top: 2px solid #d4c4a8 !important;
      max-height: none;
    }

    #map {
      height: 600mm !important;
    }

    .leaflet-popup { display: none !important; }
  }
</style>
</head>
<body>

<div class="app-container">
  <!-- TITLE BAR -->
  <header class="title-bar">
    <h1>Corredor de Conectividad Comunitaria, Herencia Ancestral y Bioeconomía<br>Colonso-Sumaco-Galeras</h1>
  </header>

  <!-- LEFT PANEL -->
  <aside class="left-panel">
    <!-- Inset Map: Ecuador -->
    <div class="panel-section">
      <h3>Ubicación en Ecuador</h3>
      <div id="insetEcuador" class="inset-map-container">
        <span class="inset-label">Ecuador</span>
      </div>
    </div>

    <!-- Inset Map: Provincial -->
    <div class="panel-section">
      <h3>Ubicación Provincial</h3>
      <div id="insetProvincial" class="inset-map-container">
        <span class="inset-label">Prov. Napo</span>
      </div>
    </div>

    <!-- Symbology / Legend -->
    <div class="panel-section">
      <h3>Simbología</h3>
      <div class="legend-item">
        <div class="legend-color" style="background: linear-gradient(135deg, #CD853F, #8B4513);"></div>
        <span>Comunidades del corredor</span>
      </div>
      <div class="legend-item">
        <div class="legend-dashed" style="border-color: #f59e0b;"></div>
        <span>Límite del Corredor NorOriental</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background: rgba(34, 139, 34, 0.35); border-color: rgba(34,139,34,0.6);"></div>
        <span>Parque Nacional Sumaco-Napo-Galeras</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background: rgba(0, 100, 200, 0.25); border-color: rgba(0,100,200,0.5);"></div>
        <span>Provincia de Napo</span>
      </div>
    </div>

    <!-- Info -->
    <div class="panel-section">
      <h3>Fundación Amazónica Yacuwarmi</h3>
      <div class="info-block">
        <strong>Contiene:</strong> Comunidades clave para fomentar acciones a favor de la bioeconomía y prácticas ancestrales con la finalidad de reforzar las áreas protegidas.
      </div>
      <div class="info-block">
        <strong>Fuente:</strong> Cartografía base esc: 1:100 000 IGM. MAATE /2024. Datos obtenidos del Sistema Único de Información Ambiental (SUIA).
      </div>
    </div>

    <!-- Technical Info -->
    <div class="panel-section">
      <h3>Sistema de Coordenadas</h3>
      <div class="info-block">
        Proyección Universal Transversa de Mercator<br>
        Elipsoide, Datum: WGS84, Zona 17 Sur
      </div>
      <div class="info-block" style="margin-top: 8px;">
        <strong>Escala de trabajo:</strong> 1:130065.355653
      </div>
      <div class="info-block">
        <strong>Fecha:</strong> 25 / 06 / 2026
      </div>
      <div class="info-block">
        <strong>Elaborado por:</strong><br>
        Ing. Tanya Camalle — Analista SIG<br>
        Ing. Kevin Castro
      </div>
    </div>

    <!-- Logos -->
    <div class="logos-section">
      <div class="logo-placeholder" style="font-size: 0.7rem;">
        🌿 YACUWARMI<br><span style="font-size: 0.5rem; font-weight: 400; color: var(--text-secondary);">Fundación Amazónica</span>
      </div>
      <div class="logos-row">
        <div class="logo-placeholder">
          Critical Ecosystem<br>Partnership Fund
        </div>
        <div class="logo-placeholder">
          Futuro<br>Latinoamericano
        </div>
      </div>
    </div>
  </aside>

  <!-- MAP AREA -->
  <main class="map-area">
    <div id="map"></div>
  </main>

  <!-- BOTTOM TABLE -->
  <footer class="bottom-bar">
    <h3>Tabla de Comunidades del Corredor</h3>
    <div class="data-table-container">
      <table class="data-table">
        <thead><tr><th>ID</th><th>Nombre</th><th>Área (ha)</th></tr></thead>
        <tbody>
          ${communityTable.filter(c => c.id <= 9).map(c => 
            \`<tr data-community-id="\${c.id}"><td>\${c.id}</td><td>\${c.name}</td><td>\${Number(c.ha).toLocaleString('es-EC', {minimumFractionDigits: 2})}</td></tr>\`
          ).join('\\n          ')}
        </tbody>
      </table>
      <table class="data-table">
        <thead><tr><th>ID</th><th>Nombre</th><th>Área (ha)</th></tr></thead>
        <tbody>
          ${communityTable.filter(c => c.id >= 10 && c.id <= 18).map(c => 
            \`<tr data-community-id="\${c.id}"><td>\${c.id}</td><td>\${c.name}</td><td>\${Number(c.ha).toLocaleString('es-EC', {minimumFractionDigits: 2})}</td></tr>\`
          ).join('\\n          ')}
        </tbody>
      </table>
      <table class="data-table">
        <thead><tr><th>ID</th><th>Nombre</th><th>Área (ha)</th></tr></thead>
        <tbody>
          ${communityTable.filter(c => c.id >= 19).map(c => 
            \`<tr data-community-id="\${c.id}"><td>\${c.id}</td><td>\${c.name}</td><td>\${Number(c.ha).toLocaleString('es-EC', {minimumFractionDigits: 2})}</td></tr>\`
          ).join('\\n          ')}
        </tbody>
      </table>
    </div>
  </footer>
</div>

<script>
// === EMBEDDED DATA ===
const communitiesGeoJSON = ${JSON.stringify(communitiesGeoJSON)};
const corridorGeoJSON = ${JSON.stringify(corridorGeoJSON)};
const communitySpecies = ${JSON.stringify(communitySpecies)};
const communityColors = ${JSON.stringify(colors)};

// === MAP INITIALIZATION ===
const map = L.map('map', {
  zoomControl: true,
  attributionControl: true,
  preferCanvas: true
});

// Satellite tile layer (Google)
L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
  maxZoom: 20,
  attribution: '&copy; Google Satellite'
}).addTo(map);

// === CORRIDOR POLYGON ===
const corridorLayer = L.geoJSON(corridorGeoJSON, {
  style: {
    color: '#f59e0b',
    weight: 2.5,
    opacity: 0.85,
    fillColor: 'transparent',
    fillOpacity: 0,
    dashArray: '10, 6',
    lineCap: 'round',
    lineJoin: 'round'
  }
}).addTo(map);

// Fit map to corridor bounds
map.fitBounds(corridorLayer.getBounds(), { padding: [20, 20] });

// === COMMUNITY POLYGONS ===
const communityLayers = {};

function getGroupClass(group) {
  const g = (group || '').toLowerCase();
  if (g === 'aves') return 'group-aves';
  if (g === 'mammalia') return 'group-mammalia';
  if (g === 'reptilia') return 'group-reptilia';
  if (g === 'amphibia') return 'group-amphibia';
  if (g === 'insecta') return 'group-insecta';
  if (g === 'plantae') return 'group-plantae';
  if (g === 'mollusca') return 'group-mollusca';
  return 'group-default';
}

function buildPopupContent(id, name, ha) {
  const data = communitySpecies[id.toString()];
  let speciesHtml = '';
  
  if (data && data.species && data.species.length > 0) {
    const cards = data.species.map(s => {
      const commonDisplay = s.common_name ? s.common_name : s.iconic_group;
      return \`
        <div class="species-card">
          <img src="\${s.photo_url}" alt="\${s.name}" loading="lazy" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iODUiPjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iODUiIGZpbGw9IiMxZjI5MzciLz48dGV4dCB4PSI2MCIgeT0iNDUiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPk5vIGltYWdlPC90ZXh0Pjwvc3ZnPg=='">
          <div class="species-info">
            <div class="species-name" title="\${s.name}">\${s.name}</div>
            <div class="species-common" title="\${commonDisplay}">\${commonDisplay}</div>
            <span class="species-group \${getGroupClass(s.iconic_group)}">\${s.iconic_group}</span>
          </div>
        </div>
      \`;
    }).join('');

    speciesHtml = \`
      <div class="popup-species-title">🌿 Especies representativas (\${data.total} observaciones)</div>
      <div class="species-grid">\${cards}</div>
    \`;
  } else {
    speciesHtml = '<div class="no-species">No hay datos de especies disponibles para esta comunidad.</div>';
  }

  return \`
    <div class="popup-header">
      <h2>📍 \${name}</h2>
      <div class="popup-meta">ID: <span>\${id}</span> &nbsp;|&nbsp; Área: <span>\${Number(ha).toLocaleString('es-EC', {minimumFractionDigits: 2})} ha</span></div>
    </div>
    \${speciesHtml}
  \`;
}

L.geoJSON(communitiesGeoJSON, {
  style: function(feature) {
    const idx = (feature.properties.id - 1) % communityColors.length;
    return {
      color: '#ffffff',
      weight: 1.5,
      opacity: 0.6,
      fillColor: communityColors[idx],
      fillOpacity: 0.65
    };
  },
  onEachFeature: function(feature, layer) {
    const props = feature.properties;
    communityLayers[props.id] = layer;

    // Popup
    layer.bindPopup(buildPopupContent(props.id, props.name, props.ha), {
      maxWidth: 440,
      maxHeight: 500,
      className: 'custom-popup'
    });

    // Hover effects
    layer.on('mouseover', function(e) {
      this.setStyle({ weight: 3, opacity: 1, fillOpacity: 0.85 });
      this.bringToFront();
    });

    layer.on('mouseout', function(e) {
      this.setStyle({ weight: 1.5, opacity: 0.6, fillOpacity: 0.65 });
    });

    // Community ID label
    const centroid = props.centroid;
    if (centroid) {
      const marker = L.marker([centroid[1], centroid[0]], {
        icon: L.divIcon({
          className: 'community-label',
          html: props.id.toString(),
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        })
      }).addTo(map);
    }
  }
}).addTo(map);

// === PARK LABEL ===
L.marker([-0.58, -77.58], {
  icon: L.divIcon({
    className: 'park-label',
    html: 'Parque Nacional<br>Sumaco-Napo-Galeras',
    iconSize: [250, 50],
    iconAnchor: [125, 25]
  })
}).addTo(map);

// === SCALE BAR ===
L.control.scale({
  imperial: false,
  maxWidth: 200,
  position: 'bottomleft'
}).addTo(map);

// === INSET MAP: ECUADOR ===
const insetEcuador = L.map('insetEcuador', {
  zoomControl: false,
  attributionControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  touchZoom: false,
  boxZoom: false,
  keyboard: false
}).setView([-1.8, -78.5], 6);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  maxZoom: 19
}).addTo(insetEcuador);

// Marker for corridor location
L.circleMarker([-0.65, -77.55], {
  radius: 6,
  color: '#f59e0b',
  fillColor: '#f59e0b',
  fillOpacity: 0.8,
  weight: 2
}).addTo(insetEcuador);

// === INSET MAP: PROVINCIAL ===
const insetProvincial = L.map('insetProvincial', {
  zoomControl: false,
  attributionControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  touchZoom: false,
  boxZoom: false,
  keyboard: false
}).setView([-0.65, -77.55], 9);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  maxZoom: 19
}).addTo(insetProvincial);

// Simplified corridor outline on inset
L.rectangle([
  [${corridorData.bbox.south}, ${corridorData.bbox.west}],
  [${corridorData.bbox.north}, ${corridorData.bbox.east}]
], {
  color: '#f59e0b',
  weight: 2,
  fillColor: '#f59e0b',
  fillOpacity: 0.15,
  dashArray: '4,4'
}).addTo(insetProvincial);

// === TABLE ROW CLICK INTERACTION ===
document.querySelectorAll('.data-table tr[data-community-id]').forEach(row => {
  row.addEventListener('click', function() {
    const id = parseInt(this.dataset.communityId);
    const layer = communityLayers[id];
    if (layer) {
      map.fitBounds(layer.getBounds(), { padding: [50, 50], maxZoom: 14 });
      layer.openPopup();
    }
  });
});
<\/script>

</body>
</html>`;

fs.writeFileSync(path.join(baseDir, 'mapa_corredor_biodiversidad.html'), html, 'utf8');
console.log('✅ HTML file generated successfully!');
console.log('   Output: mapa_corredor_biodiversidad.html');
console.log('   Communities: ' + communitiesData.length);
console.log('   Corridor points: ' + corridorData.rings[0].length);
console.log('   Species data for ' + Object.keys(communitySpecies).length + ' communities');
