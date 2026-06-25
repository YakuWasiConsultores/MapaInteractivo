import json
import os

base_dir = r'H:\Yakuwarmi\mapas interactivos'

# Read data files
with open(os.path.join(base_dir, 'communities_geo.json'), 'r', encoding='utf-8') as f:
    communities_data = json.load(f)

with open(os.path.join(base_dir, 'corridor_polygon.json'), 'r', encoding='utf-8') as f:
    corridor_data = json.load(f)

with open(os.path.join(base_dir, 'inaturalist_data.json'), 'r', encoding='utf-8') as f:
    inat_data = json.load(f)

# Build GeoJSON for communities
communities_geojson = {
    "type": "FeatureCollection",
    "features": []
}

for c in communities_data:
    feature = {
        "type": "Feature",
        "properties": {
            "id": c["id"],
            "name": c["name"],
            "ha": c["ha"],
            "centroid": c["centroid"]
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[coord[0], coord[1]] for coord in ring] for ring in c["rings"]]
        }
    }
    communities_geojson["features"].append(feature)

# Build GeoJSON for corridor
corridor_geojson = {
    "type": "Feature",
    "properties": {"name": "Corredor de Conectividad"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[coord[0], coord[1]] for coord in ring] for ring in corridor_data["rings"]]
    }
}

# Build species data per community (top 15)
community_species = {}
for cid, data in inat_data.get("community_species", {}).items():
    all_sp = data.get("all_species", [])[:15]
    community_species[cid] = {
        "name": data.get("name", ""),
        "total": data.get("total", 0),
        "species": [{
            "name": s["name"],
            "common_name": s.get("common_name", ""),
            "iconic_group": s.get("iconic_group", ""),
            "count": s.get("count", 0),
            "photo_url": s.get("photo_url", "")
        } for s in all_sp]
    }

# Community table data
community_table = [{"id": c["id"], "name": c["name"], "ha": c["ha"]} for c in communities_data]

colors = [
    '#8B4513', '#A0522D', '#CD853F', '#D2691E', '#B8860B',
    '#DAA520', '#BC8F8F', '#F4A460', '#DEB887', '#D2B48C',
    '#C19A6B', '#8B6914', '#A52A2A', '#CD5C5C', '#E9967A',
    '#FA8072', '#FFA07A', '#FF7F50', '#FF6347', '#CC5500',
    '#B22222', '#DC143C', '#C0392B', '#E74C3C', '#922B21'
]

# Build table rows
def format_ha(ha_str):
    try:
        val = float(ha_str)
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return ha_str

def build_table_rows(items):
    rows = []
    for c in items:
        rows.append(f'          <tr data-community-id="{c["id"]}"><td>{c["id"]}</td><td>{c["name"]}</td><td>{format_ha(c["ha"])}</td></tr>')
    return '\n'.join(rows)

table1 = build_table_rows([c for c in community_table if c["id"] <= 9])
table2 = build_table_rows([c for c in community_table if 10 <= c["id"] <= 18])
table3 = build_table_rows([c for c in community_table if c["id"] >= 19])

# Corridor bbox
bbox = corridor_data["bbox"]

html = f'''<!DOCTYPE html>
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
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  :root {{
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
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }}

  .app-container {{
    display: grid;
    grid-template-rows: auto 1fr auto;
    grid-template-columns: 320px 1fr;
    height: 100vh;
    width: 100vw;
    gap: 0;
  }}

  /* === TITLE BAR === */
  .title-bar {{
    grid-column: 1 / -1;
    background: linear-gradient(135deg, #1a1005 0%, #2d1a0a 30%, #1a1005 100%);
    border-bottom: 2px solid rgba(245, 158, 11, 0.3);
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    z-index: 100;
  }}

  .title-bar::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(245,158,11,0.06), transparent);
    animation: shimmer 8s infinite linear;
  }}

  @keyframes shimmer {{
    0%, 100% {{ transform: translateX(-100%); }}
    50% {{ transform: translateX(100%); }}
  }}

  .title-bar h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.35rem;
    font-weight: 900;
    text-align: center;
    background: var(--gradient-title);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 2px;
    text-transform: uppercase;
    line-height: 1.35;
    position: relative;
    z-index: 1;
  }}

  /* === LEFT PANEL === */
  .left-panel {{
    background: var(--gradient-card);
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--border-glass);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0;
    z-index: 50;
  }}

  .left-panel::-webkit-scrollbar {{ width: 4px; }}
  .left-panel::-webkit-scrollbar-track {{ background: transparent; }}
  .left-panel::-webkit-scrollbar-thumb {{ background: rgba(245,158,11,0.3); border-radius: 2px; }}

  .panel-section {{
    padding: 14px 16px;
    border-bottom: 1px solid var(--border-glass);
  }}

  .panel-section h3 {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--accent-gold);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .panel-section h3::before {{
    content: '';
    width: 3px;
    height: 14px;
    background: var(--gradient-title);
    border-radius: 2px;
    flex-shrink: 0;
  }}

  .inset-map-container {{
    width: 100%;
    height: 130px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border-glass);
    margin-bottom: 8px;
    position: relative;
  }}

  .inset-map-container .inset-label {{
    position: absolute;
    bottom: 4px;
    left: 4px;
    background: rgba(0,0,0,0.75);
    color: #fff;
    font-size: 0.58rem;
    padding: 2px 6px;
    border-radius: 3px;
    z-index: 1000;
    pointer-events: none;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    font-size: 0.7rem;
    color: var(--text-secondary);
  }}

  .legend-color {{
    width: 18px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.15);
    flex-shrink: 0;
  }}

  .legend-dashed {{
    width: 18px;
    height: 0;
    border-top: 2px dashed;
    flex-shrink: 0;
  }}

  .info-block {{
    font-size: 0.66rem;
    color: var(--text-secondary);
    line-height: 1.55;
    margin-bottom: 5px;
  }}

  .info-block strong {{
    color: var(--text-primary);
    font-weight: 600;
  }}

  .logos-section {{
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: auto;
    border-top: 1px solid var(--border-glass);
  }}

  .logo-placeholder {{
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border-glass);
    border-radius: 6px;
    padding: 8px 12px;
    text-align: center;
    font-size: 0.62rem;
    font-weight: 700;
    color: var(--accent-gold);
    letter-spacing: 1px;
    text-transform: uppercase;
  }}

  .logos-row {{
    display: flex;
    gap: 6px;
    align-items: stretch;
  }}

  .logos-row .logo-placeholder {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 38px;
    font-size: 0.53rem;
  }}

  /* === MAP AREA === */
  .map-area {{
    position: relative;
    display: flex;
    flex-direction: column;
  }}

  #map {{
    flex: 1;
    z-index: 1;
  }}

  .leaflet-container {{
    background: #0a0f1a;
    font-family: 'Inter', sans-serif;
  }}

  .community-label {{
    background: rgba(0, 0, 0, 0.8);
    border: 1.5px solid rgba(245, 158, 11, 0.6);
    border-radius: 50%;
    color: #f59e0b;
    font-size: 10px;
    font-weight: 800;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 2px 8px rgba(0,0,0,0.6);
    pointer-events: none;
  }}

  .park-label {{
    background: none !important;
    border: none !important;
    color: rgba(255, 255, 255, 0.75);
    font-size: 15px;
    font-weight: 700;
    font-family: 'Playfair Display', serif;
    text-shadow: 2px 2px 6px rgba(0,0,0,0.9), -1px -1px 4px rgba(0,0,0,0.8);
    white-space: nowrap;
    pointer-events: none;
    letter-spacing: 2px;
  }}

  /* Custom Popup */
  .leaflet-popup-content-wrapper {{
    background: rgba(10, 15, 26, 0.97) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 12px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.7), var(--shadow-glow) !important;
    color: var(--text-primary);
    padding: 0 !important;
  }}

  .leaflet-popup-content {{
    margin: 0 !important;
    width: 420px !important;
    max-height: 480px;
    overflow-y: auto;
    font-family: 'Inter', sans-serif;
  }}

  .leaflet-popup-content::-webkit-scrollbar {{ width: 4px; }}
  .leaflet-popup-content::-webkit-scrollbar-track {{ background: transparent; }}
  .leaflet-popup-content::-webkit-scrollbar-thumb {{ background: rgba(245,158,11,0.3); border-radius: 2px; }}

  .leaflet-popup-tip {{
    background: rgba(10, 15, 26, 0.97) !important;
  }}

  .leaflet-popup-close-button {{
    color: var(--accent-gold) !important;
    font-size: 20px !important;
    top: 6px !important;
    right: 8px !important;
  }}

  .popup-header {{
    padding: 14px 18px;
    border-bottom: 1px solid var(--border-glass);
    background: linear-gradient(135deg, rgba(245,158,11,0.08), transparent);
  }}

  .popup-header h2 {{
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    font-weight: 800;
    color: var(--accent-gold);
    margin-bottom: 4px;
  }}

  .popup-header .popup-meta {{
    font-size: 0.72rem;
    color: var(--text-secondary);
  }}

  .popup-header .popup-meta span {{
    color: var(--text-primary);
    font-weight: 600;
  }}

  .popup-species-title {{
    padding: 10px 18px 4px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent-gold);
  }}

  .species-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
    padding: 8px 14px 14px;
  }}

  .species-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 7px;
    overflow: hidden;
    transition: all 0.2s ease;
    cursor: default;
  }}

  .species-card:hover {{
    border-color: rgba(245,158,11,0.4);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }}

  .species-card img {{
    width: 100%;
    height: 80px;
    object-fit: cover;
    display: block;
    background: rgba(255,255,255,0.02);
  }}

  .species-card .species-info {{
    padding: 5px 7px;
  }}

  .species-card .species-name {{
    font-size: 0.58rem;
    font-style: italic;
    color: var(--text-primary);
    line-height: 1.2;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .species-card .species-common {{
    font-size: 0.52rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .species-card .species-group {{
    display: inline-block;
    font-size: 0.48rem;
    padding: 1px 5px;
    border-radius: 3px;
    margin-top: 2px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  .group-aves {{ background: rgba(59,130,246,0.2); color: #60a5fa; }}
  .group-mammalia {{ background: rgba(239,68,68,0.2); color: #f87171; }}
  .group-reptilia {{ background: rgba(16,185,129,0.2); color: #34d399; }}
  .group-amphibia {{ background: rgba(168,85,247,0.2); color: #a78bfa; }}
  .group-insecta {{ background: rgba(245,158,11,0.2); color: #fbbf24; }}
  .group-plantae {{ background: rgba(34,197,94,0.2); color: #4ade80; }}
  .group-mollusca {{ background: rgba(236,72,153,0.2); color: #f472b6; }}
  .group-fungi {{ background: rgba(168,162,158,0.2); color: #a8a29e; }}
  .group-default {{ background: rgba(148,163,184,0.2); color: #94a3b8; }}

  .no-species {{
    padding: 20px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }}

  /* === BOTTOM TABLE === */
  .bottom-bar {{
    grid-column: 1 / -1;
    background: linear-gradient(180deg, rgba(17,24,39,0.96), rgba(10,15,26,0.99));
    border-top: 1px solid var(--border-glass);
    padding: 10px 20px 12px;
    overflow-x: auto;
    max-height: 200px;
    z-index: 50;
  }}

  .bottom-bar h3 {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--accent-gold);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .bottom-bar h3::before {{
    content: '';
    width: 3px;
    height: 14px;
    background: var(--gradient-title);
    border-radius: 2px;
  }}

  .data-table-container {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
  }}

  .data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.66rem;
  }}

  .data-table th {{
    background: rgba(245,158,11,0.08);
    color: var(--accent-gold);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.58rem;
    padding: 5px 8px;
    text-align: left;
    border-bottom: 1px solid rgba(245,158,11,0.2);
    position: sticky;
    top: 0;
  }}

  .data-table td {{
    padding: 3px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: var(--text-secondary);
  }}

  .data-table td:first-child {{
    color: var(--accent-gold);
    font-weight: 700;
    text-align: center;
    width: 28px;
  }}

  .data-table td:last-child {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
    font-weight: 500;
  }}

  .data-table tr[data-community-id] {{
    cursor: pointer;
    transition: background 0.15s;
  }}

  .data-table tr[data-community-id]:hover td {{
    background: rgba(245,158,11,0.06);
  }}

  /* Scale Bar */
  .leaflet-control-scale-line {{
    background: rgba(10,15,26,0.85) !important;
    border-color: rgba(245,158,11,0.5) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.6rem !important;
    padding: 2px 6px !important;
  }}

  .leaflet-control-attribution {{
    background: rgba(10,15,26,0.8) !important;
    color: var(--text-secondary) !important;
    font-size: 0.5rem !important;
  }}

  .leaflet-control-attribution a {{
    color: var(--accent-gold) !important;
  }}

  /* === PRINT STYLES FOR A0 === */
  @media print {{
    @page {{
      size: 1189mm 841mm landscape;
      margin: 15mm;
    }}

    body {{
      overflow: visible;
      height: auto;
      width: auto;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    .app-container {{
      height: auto;
      width: 100%;
    }}

    .bottom-bar {{ max-height: none; }}

    .leaflet-popup {{ display: none !important; }}
  }}
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
    <div class="panel-section">
      <h3>Ubicación en Ecuador</h3>
      <div id="insetEcuador" class="inset-map-container">
        <span class="inset-label">Ecuador</span>
      </div>
    </div>

    <div class="panel-section">
      <h3>Ubicación Provincial</h3>
      <div id="insetProvincial" class="inset-map-container">
        <span class="inset-label">Prov. Napo / Orellana</span>
      </div>
    </div>

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
        <div class="legend-color" style="background: rgba(34, 139, 34, 0.3); border-color: rgba(34,139,34,0.5);"></div>
        <span>Parque Nacional Sumaco-Napo-Galeras</span>
      </div>
    </div>

    <div class="panel-section">
      <h3>Fundación Amazónica Yacuwarmi</h3>
      <div class="info-block">
        <strong>Contiene:</strong> Comunidades clave para fomentar acciones a favor de la bioeconomía y prácticas ancestrales con la finalidad de reforzar las áreas protegidas.
      </div>
      <div class="info-block">
        <strong>Fuente:</strong> Cartografía base esc: 1:100 000 IGM. MAATE /2024. Datos del Sistema Único de Información Ambiental (SUIA).
      </div>
    </div>

    <div class="panel-section">
      <h3>Sistema de Coordenadas</h3>
      <div class="info-block">
        Proyección Universal Transversa de Mercator<br>
        Elipsoide, Datum: WGS84, Zona 17 Sur
      </div>
      <div class="info-block" style="margin-top: 6px;">
        <strong>Escala de trabajo:</strong> 1:130.065
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

    <div class="logos-section">
      <div class="logo-placeholder" style="font-size: 0.7rem;">
        &#127807; YACUWARMI<br><span style="font-size: 0.5rem; font-weight: 400; color: var(--text-secondary);">Fundación Amazónica</span>
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
{table1}
        </tbody>
      </table>
      <table class="data-table">
        <thead><tr><th>ID</th><th>Nombre</th><th>Área (ha)</th></tr></thead>
        <tbody>
{table2}
        </tbody>
      </table>
      <table class="data-table">
        <thead><tr><th>ID</th><th>Nombre</th><th>Área (ha)</th></tr></thead>
        <tbody>
{table3}
        </tbody>
      </table>
    </div>
  </footer>
</div>

<script>
// === EMBEDDED DATA ===
const communitiesGeoJSON = {json.dumps(communities_geojson, ensure_ascii=False)};
const corridorGeoJSON = {json.dumps(corridor_geojson, ensure_ascii=False)};
const communitySpecies = {json.dumps(community_species, ensure_ascii=False)};
const communityColors = {json.dumps(colors)};

// === MAP INITIALIZATION ===
const map = L.map('map', {{
  zoomControl: true,
  attributionControl: true,
  preferCanvas: true
}});

// Satellite tile layer
L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{
  maxZoom: 20,
  attribution: '&copy; Google Satellite'
}}).addTo(map);

// === CORRIDOR POLYGON ===
const corridorLayer = L.geoJSON(corridorGeoJSON, {{
  style: {{
    color: '#f59e0b',
    weight: 2.5,
    opacity: 0.85,
    fillColor: 'transparent',
    fillOpacity: 0,
    dashArray: '10, 6',
    lineCap: 'round',
    lineJoin: 'round'
  }}
}}).addTo(map);

map.fitBounds(corridorLayer.getBounds(), {{ padding: [20, 20] }});

// === COMMUNITY POLYGONS ===
const communityLayers = {{}};

function getGroupClass(group) {{
  const g = (group || '').toLowerCase();
  if (g === 'aves') return 'group-aves';
  if (g === 'mammalia') return 'group-mammalia';
  if (g === 'reptilia') return 'group-reptilia';
  if (g === 'amphibia') return 'group-amphibia';
  if (g === 'insecta') return 'group-insecta';
  if (g === 'plantae') return 'group-plantae';
  if (g === 'mollusca') return 'group-mollusca';
  if (g === 'fungi') return 'group-fungi';
  return 'group-default';
}}

function buildPopupContent(id, name, ha) {{
  const data = communitySpecies[id.toString()];
  let speciesHtml = '';
  
  if (data && data.species && data.species.length > 0) {{
    const cards = data.species.map(s => {{
      const commonDisplay = s.common_name ? s.common_name : s.iconic_group;
      return `
        <div class="species-card">
          <img src="${{s.photo_url}}" alt="${{s.name}}" loading="lazy" onerror="this.style.display='none'">
          <div class="species-info">
            <div class="species-name" title="${{s.name}}">${{s.name}}</div>
            <div class="species-common" title="${{commonDisplay}}">${{commonDisplay}}</div>
            <span class="species-group ${{getGroupClass(s.iconic_group)}}">${{s.iconic_group}}</span>
          </div>
        </div>
      `;
    }}).join('');

    speciesHtml = `
      <div class="popup-species-title">&#127807; Especies representativas (${{data.total}} observaciones)</div>
      <div class="species-grid">${{cards}}</div>
    `;
  }} else {{
    speciesHtml = '<div class="no-species">No hay datos de especies disponibles para esta comunidad.</div>';
  }}

  return `
    <div class="popup-header">
      <h2>&#128205; ${{name}}</h2>
      <div class="popup-meta">ID: <span>${{id}}</span> &nbsp;|&nbsp; Área: <span>${{Number(ha).toLocaleString('es-EC', {{minimumFractionDigits: 2}})}} ha</span></div>
    </div>
    ${{speciesHtml}}
  `;
}}

L.geoJSON(communitiesGeoJSON, {{
  style: function(feature) {{
    const idx = (feature.properties.id - 1) % communityColors.length;
    return {{
      color: '#ffffff',
      weight: 1.5,
      opacity: 0.55,
      fillColor: communityColors[idx],
      fillOpacity: 0.6
    }};
  }},
  onEachFeature: function(feature, layer) {{
    const props = feature.properties;
    communityLayers[props.id] = layer;

    layer.bindPopup(buildPopupContent(props.id, props.name, props.ha), {{
      maxWidth: 440,
      maxHeight: 500,
      className: 'custom-popup'
    }});

    layer.on('mouseover', function(e) {{
      this.setStyle({{ weight: 3, opacity: 1, fillOpacity: 0.82 }});
      this.bringToFront();
    }});

    layer.on('mouseout', function(e) {{
      this.setStyle({{ weight: 1.5, opacity: 0.55, fillOpacity: 0.6 }});
    }});

    const centroid = props.centroid;
    if (centroid) {{
      L.marker([centroid[1], centroid[0]], {{
        icon: L.divIcon({{
          className: 'community-label',
          html: props.id.toString(),
          iconSize: [22, 22],
          iconAnchor: [11, 11]
        }})
      }}).addTo(map);
    }}
  }}
}}).addTo(map);

// === PARK LABEL ===
L.marker([-0.56, -77.58], {{
  icon: L.divIcon({{
    className: 'park-label',
    html: 'Parque Nacional<br>Sumaco-Napo-Galeras',
    iconSize: [250, 50],
    iconAnchor: [125, 25]
  }})
}}).addTo(map);

// === SCALE BAR ===
L.control.scale({{
  imperial: false,
  maxWidth: 200,
  position: 'bottomleft'
}}).addTo(map);

// === INSET MAP: ECUADOR ===
const insetEcuador = L.map('insetEcuador', {{
  zoomControl: false,
  attributionControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  touchZoom: false,
  boxZoom: false,
  keyboard: false
}}).setView([-1.8, -78.5], 6);

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  maxZoom: 19
}}).addTo(insetEcuador);

L.circleMarker([-0.65, -77.55], {{
  radius: 6,
  color: '#f59e0b',
  fillColor: '#f59e0b',
  fillOpacity: 0.8,
  weight: 2
}}).addTo(insetEcuador);

// === INSET MAP: PROVINCIAL ===
const insetProvincial = L.map('insetProvincial', {{
  zoomControl: false,
  attributionControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  touchZoom: false,
  boxZoom: false,
  keyboard: false
}}).setView([-0.65, -77.55], 9);

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  maxZoom: 19
}}).addTo(insetProvincial);

L.rectangle([
  [{bbox["south"]}, {bbox["west"]}],
  [{bbox["north"]}, {bbox["east"]}]
], {{
  color: '#f59e0b',
  weight: 2,
  fillColor: '#f59e0b',
  fillOpacity: 0.15,
  dashArray: '4,4'
}}).addTo(insetProvincial);

// === TABLE ROW CLICK INTERACTION ===
document.querySelectorAll('.data-table tr[data-community-id]').forEach(row => {{
  row.addEventListener('click', function() {{
    const id = parseInt(this.dataset.communityId);
    const layer = communityLayers[id];
    if (layer) {{
      map.fitBounds(layer.getBounds(), {{ padding: [50, 50], maxZoom: 14 }});
      setTimeout(() => layer.openPopup(), 300);
    }}
  }});
}});
</script>

</body>
</html>'''

output_path = os.path.join(base_dir, 'mapa_corredor_biodiversidad.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"✅ HTML file generated successfully!")
print(f"   Output: {output_path}")
print(f"   File size: {file_size_mb:.2f} MB")
print(f"   Communities: {len(communities_data)}")
print(f"   Corridor points: {len(corridor_data['rings'][0])}")
print(f"   Species data for {len(community_species)} communities")
