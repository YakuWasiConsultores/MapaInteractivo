import argparse
import json
import re
import unicodedata
from pathlib import Path


parser = argparse.ArgumentParser(description="Genera el mapa HTML A0 de Yacu Warmi.")
parser.add_argument(
    "--project-root",
    type=Path,
    default=Path(__file__).resolve().parent.parent,
    help="Directorio raíz que contiene los datos procesados.",
)
parser.add_argument(
    "--output",
    type=Path,
    default=None,
    help="Ruta del HTML generado.",
)
args = parser.parse_args()
base_dir = args.project_root.resolve()
data_dir = base_dir / "data"
output_path = (args.output or base_dir / "docs" / "index.html").resolve()

# Read core data
with (data_dir / "communities_geo.json").open("r", encoding="utf-8") as f:
    communities = json.load(f)

with (data_dir / "corridor_polygon.json").open("r", encoding="utf-8") as f:
    corridor = json.load(f)

with (data_dir / "inaturalist_data.json").open("r", encoding="utf-8") as f:
    inat_data = json.load(f)


def normalize_community_name(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.upper().replace('"', "")
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    value = re.sub(r"\bCHALLWAYAKU\b", "CHALLUAYAKU", value)
    return re.sub(r"\s+", " ", value).strip()


inat_by_community_name = {
    normalize_community_name(community.get("name", "")): community
    for community in inat_data["community_species"].values()
}


def local_taxon_image(taxon_id):
    if not taxon_id:
        return ""
    image_name = f"inat_taxon_{taxon_id}_medium"
    for suffix in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = base_dir / "docs" / "assets" / "images" / f"{image_name}{suffix}"
        if candidate.exists():
            return f"assets/images/{candidate.name}"
    return ""

# Read extra layers
def load_geojson(path):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

kba_geojson = load_geojson(data_dir / "KBA.geojson")
snap_geojson = load_geojson(data_dir / "SNAP.geojson")
posibles_geojson = load_geojson(data_dir / "Posibles_comunidades.geojson")
ecu25_geojson = load_geojson(data_dir / "Ecu_25.geojson")
corredor_nor_geojson = load_geojson(data_dir / "Corredor_NorOriental.geojson")
napo_geojson = load_geojson(data_dir / "Napo.geojson")


corridor_geojson = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": corridor['rings']
        },
        "properties": {"name": "Corredor"}
    }]
}

communities_features = []
used_species = set()  # Track assigned species to avoid duplicates
for c in communities:
    c_id = str(c['id'])
    
    inat = inat_by_community_name.get(
        normalize_community_name(c["name"]),
        inat_data['community_species'].get(c_id, {})
    )
    fauna = inat.get('fauna_species', [])
    
    # Pick the first fauna species not already assigned to another community
    chosen = None
    for sp in fauna:
        species_key = sp.get('taxon_id') or sp.get('name')
        if species_key not in used_species:
            chosen = sp
            break
    # Fallback: if all fauna species are taken, use the first one anyway
    if chosen is None and fauna:
        chosen = fauna[0]
    
    if chosen:
        top_species_name = chosen['name']
        top_species_common = chosen['common_name']
        top_species_img = local_taxon_image(chosen.get('taxon_id')) or chosen.get('photo_url', '')
        used_species.add(chosen.get('taxon_id') or top_species_name)
    else:
        top_species_name = "Sin registro"
        top_species_common = ""
        top_species_img = ""
    
    feat = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": c['rings']
        },
        "properties": {
            "id": c['id'],
            "name": c['name'],
            "ha": c['ha'],
            "centroid": c['centroid'],
            "top_species_name": top_species_name,
            "top_species_common": top_species_common,
            "top_species_img": top_species_img
        }
    }
    communities_features.append(feat)

communities_geojson = {
    "type": "FeatureCollection",
    "features": communities_features
}

# Create SVG Defs for Polygon Fills
user_adjustments = {
  "1": { "x": 0, "y": 0, "z": 125, "isCircle": True },
  "16": { "x": 0, "y": 0, "z": 100, "isCircle": True },
  "17": { "x": 0, "y": 0, "z": 100, "isCircle": True },
  "18": { "x": 0, "y": 0, "z": 100, "isCircle": True },
  "19": { "x": 0, "y": -45, "z": 56, "isCircle": False },
  "23": { "x": 0, "y": 0, "z": 100, "isCircle": True }
}

svg_defs = '<svg width="0" height="0" style="position:absolute; z-index:-1;"><defs>\n'
for c in communities_features:
    img = c['properties']['top_species_img']
    cid = str(c['properties']['id'])
    
    x, y, z, is_circle = 0, 0, 100, False
    if cid in user_adjustments:
        adj = user_adjustments[cid]
        x, y, z, is_circle = adj['x'], adj['y'], adj['z'], adj['isCircle']
        
    c['properties']['is_circle'] = is_circle
    
    if img:
        w = z
        h = z
        cx = (100 - w) / 2
        cy = (100 - h) / 2
        final_x = cx + x
        final_y = cy + y
        
        svg_defs += f'''
        <pattern id="bg-{cid}" patternUnits="objectBoundingBox" width="1" height="1" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
            <image id="img-{cid}" href="{img}" x="{final_x}" y="{final_y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" />
        </pattern>
        '''
svg_defs += '''
        <pattern id="hatch-kba" width="16" height="16" patternTransform="rotate(0)" patternUnits="userSpaceOnUse">
            <line x1="8" y1="0" x2="8" y2="16" style="stroke:#8B8000; stroke-width:3" />
        </pattern>
'''
svg_defs += '</defs></svg>\n'

html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Corredor de Conectividad Comunitaria</title>
    <link rel="stylesheet" href="assets/vendor/leaflet.css" />
    <style>
        :root {{
            --bg-color: #ffffff;
            --border-color: #000000;
        }}
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Arial', sans-serif;
            background-color: #f0f0f0;
            width: 1189mm;
            height: 841mm;
            box-sizing: border-box;
        }}
        
        .page-container {{
            background: #fff;
            width: 100%;
            height: 100%;
            display: flex;
            padding: 20px;
            box-sizing: border-box;
            border: 2px solid transparent;
        }}

        @media print {{
            @page {{ size: A0 landscape; margin: 0; }}
            body {{ padding: 0; background: #fff; }}
            .no-print {{ display: none !important; }}
            .page-container {{ border: none; padding: 25px; }}
        }}
        
        .btn-print {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #27ae60;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
            z-index: 9999;
        }}
        
        /* Layout Grid */
        .left-col {{
            width: 25%;
            display: flex;
            flex-direction: column;
            gap: 20px;
            padding-right: 20px;
        }}
        .right-col {{
            width: 75%;
            display: flex;
            flex-direction: column;
            border: 2px solid #000;
        }}
        
        /* Left Column Items */
        .box-title {{
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
        }}
        .inset-map {{
            border: 2px solid #ccc;
            height: 350px;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .inset-map img {{ width: 100%; height: 100%; object-fit: cover; }}
        
        .symbology-box {{
            background: #e8e8e8;
            padding: 35px;
            flex: 1;
        }}
        .symbology-title {{ font-size: 4rem; font-weight: bold; margin-bottom: 35px; text-transform: uppercase; }}
        .symbology-item {{
            display: flex; align-items: center; gap: 24px; margin-bottom: 28px; font-size: 2.6rem;
            cursor: pointer; user-select: none; transition: opacity 0.25s ease;
            border-radius: 8px; padding: 8px 12px;
        }}
        .symbology-item:hover {{ background: rgba(0,0,0,0.07); }}
        .symbology-item.layer-off {{ opacity: 0.35; }}
        .symbology-item .symb-check {{
            width: 36px; height: 36px; border: 3px solid #555; border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0; font-size: 2rem; color: #1e8449; transition: all 0.2s ease;
            background: #fff;
        }}
        .symbology-item .symb-check.checked {{ background: #d5f5e3; border-color: #1e8449; }}
        .symb-color {{ width: 90px; height: 52px; border: 1px solid #000; flex-shrink: 0; }}
        @media print {{
            .symbology-item.layer-off {{ display: none; }}
            .symbology-item .symb-check {{ display: none; }}
        }}
        
        .yacuwarmi-box {{
            border: 2px solid #000;
            display: flex;
            flex-direction: column;
        }}
        .yacuwarmi-title {{
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-bottom: 2px solid #000;
        }}
        .yacuwarmi-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            font-size: 1.2rem;
        }}
        .yg-cell {{
            padding: 10px;
            border-bottom: 1px solid #000;
            border-right: 1px solid #000;
            line-height: 1.3;
        }}
        .yg-cell:nth-child(even) {{ border-right: none; }}
        .yg-cell.no-border-bottom {{ border-bottom: none; }}
        
        .scale-box {{
            text-align: center;
            padding: 10px 0;
            font-size: 1.4rem;
        }}
        .scale-bar {{
            width: 80%;
            height: 10px;
            background: linear-gradient(90deg, #000 50%, #fff 50%);
            border: 2px solid #000;
            margin: 10px auto;
            position: relative;
        }}
        .scale-text {{ display: flex; justify-content: space-between; width: 80%; margin: 0 auto; font-size: 1.4rem; font-weight: bold; }}
        
        .logos {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #ccc;
            padding: 15px;
            gap: 15px;
        }}
        .logos img {{
            max-width: 32%;
            height: 150px;
            object-fit: contain;
        }}
        
        /* Right Column Items */
        .map-wrapper {{
            flex: 4; /* Map takes up most of the right column */
            min-height: 800px;
            position: relative;
            background: #fafafa;
        }}
        #map {{
            width: 100%;
            height: 100%;
            background: transparent;
        }}
        .map-title-banner {{
            position: absolute;
            top: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff;
            padding: 20px 40px;
            font-size: 2.8rem;
            font-weight: bold;
            text-align: center;
            z-index: 1000;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            white-space: normal;
            width: 90%;
            border: 2px solid #000;
        }}
        
        /* Pattern for KBA */
        .kba-pattern {{
            background: repeating-linear-gradient(
                45deg,
                #e67e22,
                #e67e22 5px,
                transparent 5px,
                transparent 10px
            );
        }}
        
        /* Data Tables at Bottom Right */
        .tables-wrapper {{
            flex: 1; /* Take remaining 20% */
            display: flex;
            border-top: 2px solid #000;
            background: #fff;
            padding: 10px;
            gap: 15px;
            overflow: hidden;
        }}
        .table-col {{ flex: 1; overflow: hidden; }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 1.4rem; }}
        .data-table th, .data-table td {{ border: 2px solid #000; padding: 6px; text-align: left; }}
        .data-table th {{ font-weight: bold; background: #e8e8e8; }}
        
        /* Map Labels with Photos */
        .comm-label-icon {{ 
            display: flex; 
            align-items: center; 
            justify-content: center;
        }}
        .comm-label {{
            background: #fff;
            border: 3px solid #b7410e;
            color: #b7410e;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 24px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.6);
        }}
        .park-label {{
            color: #111;
            font-size: 25px;
            font-weight: bold;
            text-align: center;
            text-shadow: 2px 2px 5px #fff, -2px -2px 5px #fff;
        }}
        .snap-label {{
            color: #111;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            text-shadow: 1px 1px 3px #fff, -1px -1px 3px #fff;
            white-space: nowrap;
        }}
        .label-inner-top {{
            position: absolute;
            top: 3px; /* 3px from margin */
            left: 0;
            transform: translateX(-50%);
            color: #000; font-size: 14px; font-weight: bold; white-space: nowrap;
        }}
        .label-inner-bottom {{
            position: absolute;
            bottom: 3px; /* 3px from margin */
            left: 0;
            transform: translateX(-50%);
            color: #000; font-size: 14px; font-weight: bold; white-space: nowrap;
        }}
        .label-inner-left {{
            position: absolute;
            top: 0;
            left: 3px; /* 3px from margin */
            transform: translateY(-50%) rotate(-90deg);
            transform-origin: left center;
            color: #000; font-size: 14px; font-weight: bold; white-space: nowrap;
        }}
        .label-inner-right {{
            position: absolute;
            top: 0;
            right: 3px; /* 3px from margin */
            transform: translateY(-50%) rotate(90deg);
            transform-origin: right center;
            color: #000; font-size: 14px; font-weight: bold; white-space: nowrap;
        }}
    </style>
</head>
<body>
    {svg_defs}
    <button class="btn-print no-print" onclick="window.print()">🖨️ Imprimir PDF (A0)</button>

    <div class="page-container">
        <!-- COLUMNA IZQUIERDA -->
        <div class="left-col">
            <div>
                <div class="box-title">Ubicación en Ecuador</div>
                <div class="inset-map"><img src="inset_ecuador.png" alt="Ecuador"></div>
            </div>
            <div>
                <div class="box-title">Ubicación provincial</div>
                <div class="inset-map"><img src="inset_napo.png" alt="Napo"></div>
            </div>
            
            <div class="symbology-box" id="symbology-box">
                <div class="symbology-title">SIMBOLOGÍA</div>
                <div class="symbology-item" data-layer="communities" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color" style="background: #a0522d;"></div> Comunidades del corredor</div>
                <div class="symbology-item" data-layer="posibles" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color" style="background: #f5b7b1; border-color: transparent;"></div> Posibles comunidades a integrar</div>
                <div class="symbology-item" data-layer="kba" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color kba-pattern" style="border-color: #e67e22;"></div> Ecu 52 kba</div>
                <div class="symbology-item" data-layer="ecu25" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color" style="background: #1e8449;"></div> Ecu_25</div>
                <div class="symbology-item" data-layer="corredorNor" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color" style="background: transparent; border: 3px dashed #0057b8;"></div> Corredor NorOriental</div>
                <div class="symbology-item" data-layer="napo" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color" style="background: #fff; border: 1px solid #000;"></div> Napo</div>
                <div class="symbology-item" data-layer="snap" onclick="toggleLayer(this)"><div class="symb-check checked">✔</div><div class="symb-color" style="background: #a9dfbf;"></div> SNAP</div>
            </div>
            
            <div class="yacuwarmi-box">
                <div class="yacuwarmi-title">FUNDACIÓN AMAZÓNICA YACUWARMI</div>
                <div class="yacuwarmi-grid">
                    <div class="yg-cell">Contiene:<br>Comunidades clave para fomentar acciones a favor de la bioeconomía y prácticas ancestrales con la finalidad de reforzar las áreas protegidas.</div>
                    <div class="yg-cell" style="text-align: center;"><br>SISTEMA DE COORDENADAS<br><br>PROYECCIÓN UNIVERSAL TRANSVERSA DE MERCATOR<br>ELIPSOIDE, DATUM: WGS84, ZONA 17 SUR</div>
                    <div class="yg-cell">Fuente:<br>Cartografía base esc: 1: 100 000 IGM. MAATE (2024).<br>Datos obtenidos del Sistema Único de Información Ambiental (SUIA)</div>
                    <div class="yg-cell" style="text-align: center;">Fecha:<br>25 / 06 / 2026<br><br>Elaborado por: Ing Tanya Camalle Analista SIG<br>Ing Kevin Castro</div>
                </div>
            </div>
            
            <div class="scale-box">
                <div>Escala de trabajo:<br>1:100000</div>
                <div class="scale-text"><span>0</span><span>15</span><span>30 km</span></div>
                <div class="scale-bar"></div>
            </div>
            
            <div class="logos">
                <img src="assets/images/LOGO_YACU_WARMI_1.png" alt="Yacuwarmi Logo">
                <img src="assets/images/cepf-logo-large-png.png" alt="Critical Ecosystem Partnership Fund">
                <img src="assets/images/Logo FFLA-colores.png" alt="Futuro Latinoamericano">
            </div>
        </div>
        
        <!-- COLUMNA DERECHA -->
        <div class="right-col">
            <div class="map-wrapper">
                <div class="map-title-banner">CORREDOR DE CONECTIVIDAD COMUNITARIA, HERENCIA ANCESTRAL Y BIOECONOMÍA COLONSO-SUMACO-GALERAS</div>
                <div id="map"></div>
            </div>
            <div class="tables-wrapper">
"""

def create_table_html(communities_slice):
    html = "<div class='table-col'><table class='data-table'>"
    html += "<tr><th>ID</th><th>NOMBRE</th><th>ESPECIE</th></tr>"
    for c in communities_slice:
        sp_name = f"{c['top_species_common']} (<i>{c['top_species_name']}</i>)" if c['top_species_common'] else f"<i>{c['top_species_name']}</i>"
        html += f"<tr><td>{c['id']}</td><td>{c['name']}</td><td>{sp_name}</td></tr>"
    html += "</table></div>"
    return html

sorted_comms = sorted([f['properties'] for f in communities_features], key=lambda x: x['id'])
col1 = sorted_comms[:12]
col2 = sorted_comms[12:]

html_template += create_table_html(col1)
html_template += create_table_html(col2)

html_template += """
            </div>
        </div>
    </div>

    <!-- Leaflet JS -->
    <script src="assets/vendor/leaflet.js"></script>
    
    <!-- Proj4js for UTM Grid -->
    <script src="assets/vendor/proj4.js"></script>
    
    <script>
        var map = L.map('map', { 
            zoomControl: false, 
            attributionControl: false,
            dragging: false, touchZoom: false, scrollWheelZoom: false, doubleClickZoom: false, boxZoom: false, keyboard: false,
            zoomSnap: 0, /* Allow exact fractional zooming */
            zoomDelta: 0.1
        }).setView([0, 0], 2);
        
        // Final exact scale will be set at the end
        var kbaData = """ + json.dumps(kba_geojson) + """;
        var snapData = """ + json.dumps(snap_geojson) + """;
        var posiblesData = """ + json.dumps(posibles_geojson) + """;
        var ecu25Data = """ + json.dumps(ecu25_geojson) + """;
        var corredorNorData = """ + json.dumps(corredor_nor_geojson) + """;
        var napoData = """ + json.dumps(napo_geojson) + """;
        var corridorData = """ + json.dumps(corridor_geojson) + """;
        var communitiesData = """ + json.dumps(communities_geojson) + """;
        
        // Function to dynamically label polygons based on bounds center
        function labelPolygons(feature, layer) {
            if (layer.getBounds) {
                var props = feature.properties || {};
                var name = props.nombre || props.NOMBRE || props.name || props.NAME || props.nam || props.NAM || props.desc || props.DESC || '';
                
                // Special hardcoded fallback if needed, but normally shapefiles have one of these
                if (!name && feature.geometry.type === 'MultiPolygon') name = 'Área Protegida';
                
                if (name) {
                    var center = layer.getBounds().getCenter();
                    var icon = L.divIcon({
                        className: 'snap-label',
                        html: name,
                        iconSize: null
                    });
                    // Delay marker addition slightly so map is ready
                    setTimeout(() => {
                        L.marker(center, {icon: icon, interactive: false}).addTo(map);
                    }, 100);
                }
            }
        }

        var napoLayer = L.geoJSON(napoData, {
            style: { color: '#000', weight: 1, fillColor: '#ffffff', fillOpacity: 1 }
        }).addTo(map);

        var snapLayer = L.geoJSON(snapData, {
            style: { color: '#7dcea0', weight: 1, fillColor: '#a9dfbf', fillOpacity: 0.8 },
            onEachFeature: labelPolygons
        }).addTo(map);
        var snapLabels = [];

        var ecu25Layer = L.geoJSON(ecu25Data, {
            style: { color: '#145a32', weight: 1, fillColor: '#1e8449', fillOpacity: 0.9 },
            onEachFeature: labelPolygons
        }).addTo(map);
        var ecu25Labels = [];

        var corredorNorLayer = L.geoJSON(corredorNorData, {
            style: { color: '#0057b8', weight: 6, dashArray: '12, 10', fillOpacity: 0 }
        }).addTo(map);
        
        var kbaLayer = L.geoJSON(kbaData, {
            style: { color: '#e67e22', weight: 4, fillColor: 'url(#hatch-kba)', fillOpacity: 0.5 }
        }).addTo(map);
        
        var posiblesLayer = L.geoJSON(posiblesData, {
            style: { color: '#f5b7b1', weight: 1, fillColor: '#f5b7b1', fillOpacity: 0.9 }
        }).addTo(map);

        // Comunidades del Corredor
        var commLayers = {};
        var callouts = {}; // { cid: { marker: ..., line: ... } }
        var editorData = {
  "1": { "lat": -0.03, "lng": -0.035, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "2": { "lat": 0.015, "lng": -0.04, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "3": { "lat": -0.07, "lng": 0.035, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "8": { "lat": 0.085, "lng": -0.07, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "11": { "lat": 0.085, "lng": 0.055, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "14": { "lat": 0.135, "lng": 0.01, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "15": { "lat": 0.03, "lng": 0.07, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "17": { "lat": -0.06, "lng": 0.045, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "19": { "lat": -0.05, "lng": 0.06, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "21": { "lat": -0.03, "lng": 0.16, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "22": { "lat": 0.01, "lng": 0.095, "size": 240, "ix": 0, "iy": 0, "iz": 125 },
  "24": { "lat": -0.07, "lng": 0.035, "size": 220, "ix": 0, "iy": 0, "iz": 100 },
  "25": { "lat": -0.01, "lng": -0.1, "size": 220, "ix": 0, "iy": 0, "iz": 100 }
}; // MUST BE DECLARED HERE FOR drawCallout
        
        function drawCallout(feature) {
            var cid = feature.properties.id;
            var spImg = feature.properties.top_species_img;
            if (!spImg) return;
            
            var center = feature.properties.centroid;
            if(!center) return;
            var latlng = [center[1], center[0]];
            
            // Default fan offsets
            var defLat = latlng[0]; var defLng = latlng[1];
            if (cid == 1) { defLat -= 0.03; defLng -= 0.03; }
            else if (cid == 2) { defLat -= 0.02; defLng -= 0.04; }
            else if (cid == 3) { defLat -= 0.05; defLng -= 0.02; }
            else if (cid == 4) { defLat += 0.03; defLng -= 0.04; }
            else if (cid == 5) { defLat += 0.05; defLng -= 0.05; }
            else if (cid == 6) { defLat += 0.06; defLng -= 0.02; }
            else if (cid == 7) { defLat -= 0.04; defLng -= 0.04; }
            else if (cid == 8) { defLat += 0.08; defLng -= 0.03; }
            else if (cid == 9) { defLat += 0.07; defLng -= 0.01; }
            else if (cid == 10) { defLat -= 0.06; defLng -= 0.02; }
            else if (cid == 11) { defLat += 0.06; defLng += 0.02; }
            else if (cid == 12) { defLat += 0.06; defLng += 0.04; }
            else if (cid == 13) { defLat -= 0.08; defLng -= 0.04; }
            else if (cid == 14) { defLat += 0.08; defLng -= 0.02; }
            else if (cid == 15) { defLat += 0.05; defLng -= 0.03; }
            else if (cid == 16) { defLat -= 0.10; defLng -= 0.02; }
            else if (cid == 17) { defLat -= 0.10; defLng += 0.03; }
            else if (cid == 18) { defLat -= 0.14; defLng += 0.00; }
            else if (cid == 19) { defLat -= 0.08; defLng += 0.06; }
            else if (cid == 20) { defLat -= 0.06; defLng += 0.08; }
            else if (cid == 21) { defLat += 0.05; defLng += 0.05; }
            else if (cid == 22) { defLat += 0.04; defLng += 0.08; }
            else if (cid == 23) { defLat += 0.06; defLng += 0.08; }
            else if (cid == 24) { defLat -= 0.04; defLng += 0.08; }
            else if (cid == 25) { defLat += 0.06; defLng += 0.06; }
            else { defLat += 0.05; defLng += 0.05; }
            
            // Override with editorData if exists
            var adj = editorData[cid] || { lat: defLat - latlng[0], lng: defLng - latlng[1], size: 220, ix: 0, iy: 0, iz: 100 };
            
            var targetLat = latlng[0] + parseFloat(adj.lat || (defLat - latlng[0]));
            var targetLng = latlng[1] + parseFloat(adj.lng || (defLng - latlng[1]));
            var targetPoint = [targetLat, targetLng];
            
            var size = parseFloat(adj.size || 220);
            var ix = parseFloat(adj.ix || 0);
            var iy = parseFloat(adj.iy || 0);
            var iz = parseFloat(adj.iz || 100);
            
            // Remove old
            if (callouts[cid]) {
                if (callouts[cid].line) map.removeLayer(callouts[cid].line);
                if (callouts[cid].marker) map.removeLayer(callouts[cid].marker);
            }
            callouts[cid] = {};
            
            // Draw line
            if (targetLat !== latlng[0] || targetLng !== latlng[1]) {
                callouts[cid].line = L.polyline([latlng, targetPoint], {color: '#000000', weight: 4, dashArray: '6,6', opacity: 0.8}).addTo(map);
            }
            
            // Convertir background a img real para que siempre aparezca en el PDF
            var imgScale = iz / 100;
            var imgW = size * imgScale;
            var imgH = size * imgScale;
            var imgTop = (size - imgH) / 2 + iy;
            var imgLeft = (size - imgW) / 2 + ix;
            
            var iconHtml = '<div style="width:'+size+'px; height:'+size+'px; border-radius:50%; border:5px solid #000; overflow:hidden; position:relative; background:#fff; box-shadow:6px 6px 15px rgba(0,0,0,0.6); -webkit-print-color-adjust: exact; color-adjust: exact;">' +
                           '<img src="' + spImg + '" style="position:absolute; top:'+imgTop+'px; left:'+imgLeft+'px; width:'+imgW+'px; height:'+imgH+'px; max-width:none; max-height:none;">' +
                           '</div>';
            callouts[cid].marker = L.marker(targetPoint, {
                icon: L.divIcon({ className: '', html: iconHtml, iconSize: [size,size], iconAnchor: [size/2,size/2] }),
                interactive: false
            }).addTo(map);
        }

        var commLabelMarkers = [];
        var commCalloutElements = [];
        var communitiesLayer = L.geoJSON(communitiesData, {
            style: function(feature) {
                return { color: '#fff', weight: 2, fillColor: '#a0522d', fillOpacity: 0.8 };
            },
            onEachFeature: function(feature, layer) {
                commLayers[feature.properties.id] = { feature: feature, layer: layer };
                
                var center = feature.properties.centroid;
                if(center) {
                    var latlng = [center[1], center[0]];
                    var icon = L.divIcon({
                        className: 'comm-label-icon',
                        html: `<div class="comm-label">${feature.properties.id}</div>`,
                        iconSize: null,
                        iconAnchor: [22, 22]
                    });
                    var labelMk = L.marker(latlng, {icon: icon, interactive: false}).addTo(map);
                    commLabelMarkers.push(labelMk);
                    
                    drawCallout(feature);
                    // Store callout refs for toggle
                    var cid = feature.properties.id;
                    if(callouts[cid]) {
                        if(callouts[cid].marker) commCalloutElements.push(callouts[cid].marker);
                        if(callouts[cid].line) commCalloutElements.push(callouts[cid].line);
                    }
                }
            }
        }).addTo(map);
        
        // Corredor (Yellow/Orange dashed) - Represents Corredor NorOriental or main Corredor
        var corridorLayer = L.geoJSON(corridorData, {
            style: { color: '#c0392b', weight: 12, dashArray: '15, 15', fillColor: 'transparent', opacity: 1.0 }
        }).addTo(map);

        // ============ INTERACTIVE SYMBOLOGY TOGGLE ============
        var mapLayers = {
            'communities': { layer: communitiesLayer, extras: commLabelMarkers.concat(commCalloutElements).concat([corridorLayer]) },
            'posibles':    { layer: posiblesLayer, extras: [] },
            'kba':         { layer: kbaLayer, extras: [] },
            'ecu25':       { layer: ecu25Layer, extras: [] },
            'corredorNor': { layer: corredorNorLayer, extras: [] },
            'napo':        { layer: napoLayer, extras: [] },
            'snap':        { layer: snapLayer, extras: [] }
        };

        function toggleLayer(el) {
            var layerName = el.getAttribute('data-layer');
            var entry = mapLayers[layerName];
            if (!entry) return;
            var check = el.querySelector('.symb-check');
            var isOn = check.classList.contains('checked');
            if (isOn) {
                // Turn OFF
                check.classList.remove('checked');
                check.innerHTML = '';
                el.classList.add('layer-off');
                if (entry.layer && map.hasLayer(entry.layer)) map.removeLayer(entry.layer);
                entry.extras.forEach(function(m) { if (map.hasLayer(m)) map.removeLayer(m); });
            } else {
                // Turn ON
                check.classList.add('checked');
                check.innerHTML = '\u2714';
                el.classList.remove('layer-off');
                if (entry.layer && !map.hasLayer(entry.layer)) map.addLayer(entry.layer);
                entry.extras.forEach(function(m) { if (!map.hasLayer(m)) map.addLayer(m); });
            }
        }
        
        // Labels
        var parkIcon = L.divIcon({
            className: 'park-label',
            html: 'Parque Nacional<br>Sumaco-Napo Galeras',
            iconSize: [300, 80]
        });
        L.marker([-0.55, -77.65], {icon: parkIcon, interactive: false}).addTo(map);
        
        // Graticule (Grid) with coordinate labels
        proj4.defs("EPSG:32717","+proj=utm +zone=17 +south +datum=WGS84 +units=m +no_defs");
        
        function drawGrid() {
            var b = map.getBounds();
            var step = 10000; // 10km grid
            var gridFeatures = [];
            
            var swUTM = proj4("EPSG:4326", "EPSG:32717", [b.getWest(), b.getSouth()]);
            var neUTM = proj4("EPSG:4326", "EPSG:32717", [b.getEast(), b.getNorth()]);
            
            var startX = Math.floor(swUTM[0] / step) * step;
            var endX = Math.ceil(neUTM[0] / step) * step;
            var startY = Math.floor(swUTM[1] / step) * step;
            var endY = Math.ceil(neUTM[1] / step) * step;
            
            // Draw Vertical lines (X / Easting)
            for (var x = startX; x <= endX; x += step) {
                var bottom = proj4("EPSG:32717", "EPSG:4326", [x, startY - step]);
                var top = proj4("EPSG:32717", "EPSG:4326", [x, endY + step]);
                
                gridFeatures.push({ "type": "Feature", "geometry": { "type": "LineString", "coordinates": [[bottom[0], bottom[1]], [top[0], top[1]]] } });
                
                var label = x.toString();
                // Place exactly at top edge
                var topEdge = proj4("EPSG:32717", "EPSG:4326", [x, neUTM[1]]);
                var htmlTop = '<div class="label-inner-top">' + label + '</div>';
                L.marker([b.getNorth(), topEdge[0]], {icon: L.divIcon({ html: htmlTop, iconSize: [0,0] }), interactive: false}).addTo(map);
                
                // Place exactly at bottom edge
                var bottomEdge = proj4("EPSG:32717", "EPSG:4326", [x, swUTM[1]]);
                var htmlBottom = '<div class="label-inner-bottom">' + label + '</div>';
                L.marker([b.getSouth(), bottomEdge[0]], {icon: L.divIcon({ html: htmlBottom, iconSize: [0,0] }), interactive: false}).addTo(map);
            }
            
            // Draw Horizontal lines (Y / Northing)
            for (var y = startY; y <= endY; y += step) {
                var left = proj4("EPSG:32717", "EPSG:4326", [startX - step, y]);
                var right = proj4("EPSG:32717", "EPSG:4326", [endX + step, y]);
                
                gridFeatures.push({ "type": "Feature", "geometry": { "type": "LineString", "coordinates": [[left[0], left[1]], [right[0], right[1]]] } });
                
                var label = y.toString();
                // Place exactly at left edge (ascending vertical)
                var leftEdge = proj4("EPSG:32717", "EPSG:4326", [swUTM[0], y]);
                var htmlLeft = '<div class="label-inner-left">' + label + '</div>';
                L.marker([leftEdge[1], b.getWest()], {icon: L.divIcon({ html: htmlLeft, iconSize: [0,0] }), interactive: false}).addTo(map);
                
                // Place exactly at right edge (descending vertical)
                var rightEdge = proj4("EPSG:32717", "EPSG:4326", [neUTM[0], y]);
                var htmlRight = '<div class="label-inner-right">' + label + '</div>';
                L.marker([rightEdge[1], b.getEast()], {icon: L.divIcon({ html: htmlRight, iconSize: [0,0] }), interactive: false}).addTo(map);
            }
            
            L.geoJSON(gridFeatures, {
                style: { color: '#000', weight: 1, dashArray: '4, 4', opacity: 0.4 },
                interactive: false
            }).addTo(map);
        }
            
        // Calculate exact zoom for 1:70,000 scale at 96 DPI (Standard CSS print DPI)
        var bounds = L.geoJSON(communitiesData).getBounds();
        var center = bounds.getCenter();
        
        var desiredScale = 100000;
        var earthCircumference = 40075016; // in meters
        var dpi = 96;
        var pxPerMeter = dpi * 39.3701;
        var scaleAtZoom0 = (earthCircumference * Math.cos(center.lat * Math.PI / 180) * pxPerMeter) / 256;
        var exactZoom = Math.log2(scaleAtZoom0 / desiredScale);
        
        // Set exact scale and center
        map.setView(center, exactZoom);
        
        // Draw grid after map has resized and fit bounds
        setTimeout(drawGrid, 500);
        
        // --- LIVE EDITOR ---
        var currentEditFeature = null;
        var currentEditLayer = null;
        var floatingCircles = {};
        
        var editorHtml = `
        <div id="img-editor-panel" class="no-print" style="position:fixed; bottom:50px; left:50px; background:white; padding:15px; border:3px solid #000; z-index:10000; border-radius:10px; box-shadow:5px 5px 15px rgba(0,0,0,0.5);">
            <div class="map-controls">
                <label><b>Editor de burbujas</b></label>
                <div style="margin-top:10px;">
                    <select id="commSelect" style="width:100%; padding:5px; margin-bottom:10px;">
                        <option value="">-- Seleccionar --</option>
                    </select>
                </div>
                
                <div id="slidersPanel" style="display:none;">
                    <label>Mover Arriba/Abajo (Latitud): <span id="valLat">0</span></label>
                    <input type="range" id="sliderLat" min="-0.3" max="0.3" step="0.005" value="0">
                    
                    <label>Mover Izq/Der (Longitud): <span id="valLng">0</span></label>
                    <input type="range" id="sliderLng" min="-0.3" max="0.3" step="0.005" value="0">
                    
                    <label>Tamaño Burbuja: <span id="valSize">220</span>px</label>
                    <input type="range" id="sliderSize" min="50" max="400" step="10" value="220">
                    
                    <label>Encuadrar Foto X: <span id="valImgX">0</span></label>
                    <input type="range" id="sliderImgX" min="-100" max="100" step="5" value="0">
                    
                    <label>Encuadrar Foto Y: <span id="valImgY">0</span></label>
                    <input type="range" id="sliderImgY" min="-100" max="100" step="5" value="0">
                    
                    <label>Zoom Foto: <span id="valImgZ">100</span>%</label>
                    <input type="range" id="sliderImgZ" min="50" max="300" step="5" value="100">
                </div>
                
                <button onclick="exportData()" style="width:100%; padding:10px; margin-top:15px; background:#e74c3c; color:white; border:none; font-weight:bold; cursor:pointer;">Exportar Ajustes</button>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', editorHtml);
        
        var selectEl = document.getElementById('commSelect');
        var ids = Object.keys(commLayers).sort(function(a,b){return parseInt(a)-parseInt(b)});
        for(var i=0; i<ids.length; i++) {
            var key = ids[i];
            if(commLayers[key].feature.properties.top_species_img) {
                var opt = document.createElement('option');
                opt.value = key;
                opt.innerText = 'ID ' + key + ' - ' + commLayers[key].feature.properties.name;
                selectEl.appendChild(opt);
            }
        }
        
        var currentEditId = null;
        var sliderLat = document.getElementById('sliderLat');
        var sliderLng = document.getElementById('sliderLng');
        var sliderSize = document.getElementById('sliderSize');
        var sliderImgX = document.getElementById('sliderImgX');
        var sliderImgY = document.getElementById('sliderImgY');
        var sliderImgZ = document.getElementById('sliderImgZ');
        
        var valLat = document.getElementById('valLat');
        var valLng = document.getElementById('valLng');
        var valSize = document.getElementById('valSize');
        var valImgX = document.getElementById('valImgX');
        var valImgY = document.getElementById('valImgY');
        var valImgZ = document.getElementById('valImgZ');

        selectEl.addEventListener('change', function(e) {
            var key = e.target.value;
            if(!key) {
                document.getElementById('slidersPanel').style.display = 'none';
                currentEditId = null;
                return;
            }
            currentEditId = key;
            document.getElementById('slidersPanel').style.display = 'block';
            
            var feat = commLayers[key].feature;
            var spImg = feat.properties.top_species_img;
            if(!spImg) {
                document.getElementById('slidersPanel').style.display = 'none';
                return;
            }
            
            var latlng = [feat.properties.centroid[1], feat.properties.centroid[0]];
            // Default fan offsets (same logic as drawCallout)
            var defLat = latlng[0]; var defLng = latlng[1];
            var cid = parseInt(key);
            if (cid == 1) { defLat -= 0.03; defLng -= 0.03; }
            else if (cid == 2) { defLat -= 0.02; defLng -= 0.04; }
            else if (cid == 3) { defLat -= 0.05; defLng -= 0.02; }
            else if (cid == 4) { defLat += 0.03; defLng -= 0.04; }
            else if (cid == 5) { defLat += 0.05; defLng -= 0.05; }
            else if (cid == 6) { defLat += 0.06; defLng -= 0.02; }
            else if (cid == 7) { defLat -= 0.04; defLng -= 0.04; }
            else if (cid == 8) { defLat += 0.08; defLng -= 0.03; }
            else if (cid == 9) { defLat += 0.07; defLng -= 0.01; }
            else if (cid == 10) { defLat -= 0.06; defLng -= 0.02; }
            else if (cid == 11) { defLat += 0.06; defLng += 0.02; }
            else if (cid == 12) { defLat += 0.06; defLng += 0.04; }
            else if (cid == 13) { defLat -= 0.08; defLng -= 0.04; }
            else if (cid == 14) { defLat += 0.08; defLng -= 0.02; }
            else if (cid == 15) { defLat += 0.05; defLng -= 0.03; }
            else if (cid == 16) { defLat -= 0.10; defLng -= 0.02; }
            else if (cid == 17) { defLat -= 0.10; defLng += 0.03; }
            else if (cid == 18) { defLat -= 0.14; defLng += 0.00; }
            else if (cid == 19) { defLat -= 0.08; defLng += 0.06; }
            else if (cid == 20) { defLat -= 0.06; defLng += 0.08; }
            else if (cid == 21) { defLat += 0.05; defLng += 0.05; }
            else if (cid == 22) { defLat += 0.04; defLng += 0.08; }
            else if (cid == 23) { defLat += 0.06; defLng += 0.08; }
            else if (cid == 24) { defLat -= 0.04; defLng += 0.08; }
            else if (cid == 25) { defLat += 0.06; defLng += 0.06; }
            else { defLat += 0.05; defLng += 0.05; }
            
            var adj = editorData[key] || { lat: defLat - latlng[0], lng: defLng - latlng[1], size: 220, ix: 0, iy: 0, iz: 100 };
            
            sliderLat.value = adj.lat; valLat.innerText = parseFloat(adj.lat).toFixed(3);
            sliderLng.value = adj.lng; valLng.innerText = parseFloat(adj.lng).toFixed(3);
            sliderSize.value = adj.size; valSize.innerText = adj.size;
            sliderImgX.value = adj.ix; valImgX.innerText = adj.ix;
            sliderImgY.value = adj.iy; valImgY.innerText = adj.iy;
            sliderImgZ.value = adj.iz; valImgZ.innerText = adj.iz;
        });

        function applyLiveEdit() {
            if(!currentEditId) return;
            
            editorData[currentEditId] = {
                lat: parseFloat(sliderLat.value),
                lng: parseFloat(sliderLng.value),
                size: parseInt(sliderSize.value),
                ix: parseInt(sliderImgX.value),
                iy: parseInt(sliderImgY.value),
                iz: parseInt(sliderImgZ.value)
            };
            
            drawCallout(commLayers[currentEditId].feature);
        }

        sliderLat.addEventListener('input', function(e) { valLat.innerText = parseFloat(e.target.value).toFixed(3); applyLiveEdit(); });
        sliderLng.addEventListener('input', function(e) { valLng.innerText = parseFloat(e.target.value).toFixed(3); applyLiveEdit(); });
        sliderSize.addEventListener('input', function(e) { valSize.innerText = e.target.value; applyLiveEdit(); });
        sliderImgX.addEventListener('input', function(e) { valImgX.innerText = e.target.value; applyLiveEdit(); });
        sliderImgY.addEventListener('input', function(e) { valImgY.innerText = e.target.value; applyLiveEdit(); });
        sliderImgZ.addEventListener('input', function(e) { valImgZ.innerText = e.target.value; applyLiveEdit(); });
        
        function exportData() {
            var txt = JSON.stringify(editorData, null, 2);
            var ta = document.createElement('textarea');
            ta.value = txt;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            alert('Ajustes copiados al portapapeles.\\n\\nPégalos en el chat:\\n\\n' + txt);
        }
        
    </script>
</body>
</html>
"""

output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8") as f:
    f.write(html_template)

print(f"HTML generado: {output_path}")
