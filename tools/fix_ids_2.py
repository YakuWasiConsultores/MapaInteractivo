import json
with open(r'H:\Yakuwarmi\mapas interactivos\communities_geo.json', 'r', encoding='utf-8') as f: data = json.load(f)
for c in data:
    if 'VOLC' in c['name'] and 'SUMACO' in c['name']:
        c['id'] = 8
        c['name'] = 'COMUNIDAD KICHWA VOLCÁN SUMACO'
    if 'ACOKI' in c['name']:
        c['id'] = 6
        c['name'] = 'ASOCIACION DE COMUNIDADES KIJUS "ACOKI"'
    if 'BIGAL' in c['name']:
        c['id'] = 23
        c['name'] = 'RESERVA BIOLOGICA RÍO BIGAL'

data.sort(key=lambda x: x['id'])
with open(r'H:\Yakuwarmi\mapas interactivos\communities_geo.json', 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
