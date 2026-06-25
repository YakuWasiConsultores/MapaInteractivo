import xml.etree.ElementTree as ET
qgs_path = r'H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\PROYECTO\Corredor_de_conectividad_7_20260622_1524.qgs'
tree = ET.parse(qgs_path)
root = tree.getroot()

print('--- ALL LAYERS IN QGIS PROJECT ---')
for layer in root.findall('.//maplayer'):
    name = layer.find('layername').text if layer.find('layername') is not None else 'Unknown'
    source = layer.find('datasource').text if layer.find('datasource') is not None else 'Unknown'
    print(f'Layer: {name} -> {source}')
