import xml.etree.ElementTree as ET
import json

tree = ET.parse(r'H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\GEOPACKAGE\ESTILOS\Comunidades_del_corredor-25.qml')
root = tree.getroot()
renderer = root.find('.//renderer-v2')

symbol_colors = {}
for sym in renderer.findall('.//symbol'):
    name = sym.get('name')
    for prop in sym.findall('.//prop'):
        if prop.get('k') == 'color':
            # Format is typically "R,G,B,A"
            rgba = prop.get('v').split(',')
            if len(rgba) >= 3:
                r, g, b = int(rgba[0]), int(rgba[1]), int(rgba[2])
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                symbol_colors[name] = hex_color

cat_colors = {}
for cat in renderer.findall('.//category'):
    val = cat.get('value')
    label = cat.get('label')
    sym = cat.get('symbol')
    if sym in symbol_colors:
        cat_colors[label] = symbol_colors[sym]

print("Extracted Colors:")
for k, v in cat_colors.items():
    print(f"{k}: {v}")

with open(r'H:\Yakuwarmi\mapas interactivos\colors.json', 'w', encoding='utf-8') as f:
    json.dump(cat_colors, f, indent=2, ensure_ascii=False)
