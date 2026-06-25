import json

name_map = {
    'MUNAY SUYU': 4,
    'PACTO SUMACO': 11,
    'CENTRO KICHWA RIO GAUCAMAYOS': 14,
    'COMUNA JUAN PIO MONTUFAR': 24,
    'PUEBLO KICHWA WAMANI PUKIWA': 10,
    'COMUNIDAD KICHWA CHALLUAYAKU': 7,
    'COMUNA KICHWA SANTA ROSA DE ARAPINO': 19,
    'COMUNA 24 DE MAYO': 20,
    'PREDIOS PRIVADOS': 17,
    'ASOCIACION DE TRABAJADORES AGRICOLAS - AUTONOMOS DE SARDINAS': 5,
    'COMUNA SAN JOSE DE PAYAMINO': 25,
    'COMUNIDAD KICHWA SANTA RITA': 1,
    'COMUNIDAD KICHWA CHAKA YAKU': 21,
    'CENTRO URBANO HUATICOCHA': 18,
    'COMUNIDAD KICHWA VOLCN SUMACO': 8,
    'COMUNA AVILA VIEJO': 22,
    'COMUNIDAD KICHWA JATUN SUMAKU': 13,
    'COMUNIDAD SAN FRANCISCO DE COTUNDO': 2,
    'ASOCIACIN DE COMUNIDADES KIJUS "ACOKI"': 6,
    'COMUNIDAD KICHWA WAWA SUMACO': 12,
    'PASOHURCU (PREDIOS INDIVIDUALES)': 15,
    'LA FLORESTA  (PREDIOS INDIVIDUALES)': 16,
    'COMUNIDAD KICHWA PUCUNO CHICO': 9,
    'COMUNIDAD NUEVA ESPERANZA': 3,
    'RESERVA BIOLOGICA RO BIGAL': 23
}

official_names = {
    4: 'MUNAY SUYU',
    11: 'PACTO SUMACO',
    14: 'CENTRO KICHWA RIO GAUCAMAYOS',
    24: 'COMUNA JUAN PIO MONTUFAR',
    10: 'PUEBLO KICHWA WAMANI PUKIWA',
    7: 'COMUNIDAD KICHWA CHALLWAYAKU',
    19: 'COMUNA KICHWA SANTA ROSA DE ARAPINO',
    20: 'COMUNA 24 DE MAYO',
    17: 'PREDIOS PRIVADOS',
    5: 'ASOCIACION DE TRABAJADORES AGRICOLAS AUTONOMOS DE SARDINAS',
    25: 'COMUNA SAN JOSE DE PAYAMINO',
    1: 'COMUNIDAD KICHWA SANTA RITA',
    21: 'COMUNIDAD KICHWA CHAKA YAKU',
    18: 'CENTRO URBANO HUATICOCHA',
    8: 'COMUNIDAD KICHWA VOLCÁN SUMACO',
    22: 'COMUNA AVILA VIEJO',
    13: 'COMUNIDAD KICHWA JATUN SUMAKU',
    2: 'COMUNIDAD SAN FRANCISCO DE COTUNDO',
    6: 'ASOCIACION DE COMUNIDADES KIJUS "ACOKI"',
    12: 'COMUNIDAD KICHWA WAWA SUMACO',
    15: 'PASOHURCU (PREDIOS INDIVIDUALES)',
    16: 'LA FLORESTA (PREDIOS INDIVIDUALES)',
    9: 'COMUNIDAD KICHWA PUCUNO CHICO',
    3: 'COMUNIDAD NUEVA ESPERANZA',
    23: 'RESERVA BIOLOGICA RÍO BIGAL'
}

with open(r'H:\Yakuwarmi\mapas interactivos\communities_geo.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for c in data:
    # also try direct match if encoding fails
    n = c['name']
    if n in name_map:
        new_id = name_map[n]
    else:
        # fuzzy match
        for k, v in name_map.items():
            if k.replace('', '') in n.replace('', ''):
                new_id = v
                break
        else:
            print(f"NOT FOUND: {n}")
            continue

    c['id'] = new_id
    c['name'] = official_names[new_id]

# sort the json by ID
data.sort(key=lambda x: x['id'])

with open(r'H:\Yakuwarmi\mapas interactivos\communities_geo.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Updated communities_geo.json')
