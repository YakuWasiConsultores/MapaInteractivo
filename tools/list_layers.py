import xml.etree.ElementTree as ET

tree = ET.parse(r'H:\Yakuwarmi\mapas interactivos\qgz_extracted\Corredor_de_conectividad_7_20260622_1524.qgs')
root = tree.getroot()

# List all layers with full detail
print("=== ALL LAYERS ===")
for i, layer in enumerate(root.findall('.//maplayer')):
    name = layer.find('layername')
    ltype = layer.get('type')
    geom = layer.get('geometry')
    source = layer.find('datasource')
    layer_name = name.text if name is not None else "unknown"
    src = source.text if source is not None and source.text else "N/A"
    print(f"\n[{i}] {layer_name}")
    print(f"    Type: {ltype} | Geometry: {geom}")
    print(f"    Source: {src[:400]}")

# List layout names
print("\n\n=== LAYOUT NAMES ===")
for layout in root.findall('.//Layout'):
    lname = layout.get('name', 'unnamed')
    print(f"  - {lname}")
