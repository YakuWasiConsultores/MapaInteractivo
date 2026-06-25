import xml.etree.ElementTree as ET

tree = ET.parse(r'H:\Yakuwarmi\mapas interactivos\qgz_extracted\Corredor_de_conectividad_7_20260622_1524.qgs')
root = tree.getroot()

# Project title
title = root.find('.//title')
print("Project title:", title.text if title is not None else "N/A")

# List all layers
print("\n=== LAYERS ===")
for layer in root.findall('.//maplayer'):
    name = layer.find('layername')
    ltype = layer.get('type')
    geom = layer.get('geometry')
    source = layer.find('datasource')
    layer_name = name.text if name is not None else "unknown"
    print(f"  Layer: {layer_name}")
    print(f"    Type: {ltype} | Geometry: {geom}")
    if source is not None and source.text:
        src_text = source.text[:300]
        print(f"    Source: {src_text}")
    print()

# Layout/Composer info
print("\n=== LAYOUTS ===")
for layout in root.findall('.//Layout'):
    lname = layout.get('name', 'unnamed')
    units = layout.get('units', '?')
    print(f"  Layout: {lname} | Units: {units}")
    
    # Page size
    for page in layout.findall('.//LayoutItem[@type="65638"]'):
        size = page.find('.//LayoutObject/dataDefinedProperties')
        w = page.get('size', '')
        print(f"    Page size attr: {w}")
    
    # All items
    for item in layout.findall('.//LayoutItem'):
        itype = item.get('type', '?')
        iid = item.get('id', '?')
        uuid = item.get('uuid', '')
        pos = item.get('position', '')
        size = item.get('size', '')
        print(f"    Item type={itype} id={iid} pos={pos} size={size}")

# Also look for print layouts in older format
print("\n=== COMPOSERS (old format) ===")
for comp in root.findall('.//Composer'):
    print(f"  Composer: {comp.get('title', 'untitled')}")
