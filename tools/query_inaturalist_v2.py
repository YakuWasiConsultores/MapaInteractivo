"""
Query iNaturalist per community - fixed version without iconic_taxa filter.
Also expand bbox slightly for small communities.
"""
import json
import urllib.request
import urllib.parse
import time

with open(r"H:\Yakuwarmi\mapas interactivos\communities_geo.json", 'r', encoding='utf-8') as f:
    communities = json.load(f)

# Load existing global data
with open(r"H:\Yakuwarmi\mapas interactivos\inaturalist_data.json", 'r', encoding='utf-8') as f:
    existing = json.load(f)

base_url = "https://api.inaturalist.org/v1/observations/species_counts"
results_by_community = {}

print("=== QUERYING PER COMMUNITY (ALL TAXA) ===")
for comm in communities:
    bbox = comm['bbox_wgs84']
    comm_name = comm['name']
    comm_id = comm['id']
    
    # Expand small bboxes slightly (add ~500m buffer)
    buffer = 0.005  # ~500m
    s = bbox['south'] - buffer
    n = bbox['north'] + buffer
    w = bbox['west'] - buffer
    e = bbox['east'] + buffer
    
    params = {
        'swlat': f"{s:.5f}",
        'swlng': f"{w:.5f}",
        'nelat': f"{n:.5f}",
        'nelng': f"{e:.5f}",
        'quality_grade': 'research',
        'per_page': '15',
        'order': 'desc',
        'order_by': 'count',
        'locale': 'es'
    }
    
    url = base_url + "?" + urllib.parse.urlencode(params)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Yakuwarmi-Corredor/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        
        all_species = []
        fauna_species = []
        for r in data.get('results', []):
            taxon = r.get('taxon', {})
            count = r.get('count', 0)
            photo_url = ''
            if taxon.get('default_photo'):
                photo_url = taxon['default_photo'].get('medium_url', '')
            
            sp = {
                'taxon_id': taxon.get('id'),
                'name': taxon.get('name', ''),
                'common_name': taxon.get('preferred_common_name', ''),
                'rank': taxon.get('rank', ''),
                'iconic_group': taxon.get('iconic_taxon_name', ''),
                'count': count,
                'photo_url': photo_url
            }
            all_species.append(sp)
            if sp['iconic_group'] in ('Mammalia', 'Aves', 'Reptilia', 'Amphibia'):
                fauna_species.append(sp)
        
        results_by_community[str(comm_id)] = {
            'name': comm_name,
            'total': data.get('total_results', 0),
            'all_species': all_species,
            'fauna_species': fauna_species
        }
        
        top_fauna = fauna_species[0] if fauna_species else None
        top_all = all_species[0] if all_species else None
        total = data.get('total_results', 0)
        
        if top_fauna:
            print(f"  [{comm_id:2d}] {comm_name[:45]:45s} | {total:4d} spp | Fauna: {top_fauna['name']} ({top_fauna['common_name']})")
        elif top_all:
            print(f"  [{comm_id:2d}] {comm_name[:45]:45s} | {total:4d} spp | Top: {top_all['name']} ({top_all['iconic_group']})")
        else:
            print(f"  [{comm_id:2d}] {comm_name[:45]:45s} | {total:4d} spp | No observations")
        
    except Exception as ex:
        print(f"  [{comm_id:2d}] {comm_name}: Error - {ex}")
        results_by_community[str(comm_id)] = {'name': comm_name, 'total': 0, 'all_species': [], 'fauna_species': []}
    
    time.sleep(0.5)

# Update existing data
existing['community_species'] = results_by_community
out_path = r"H:\Yakuwarmi\mapas interactivos\inaturalist_data.json"
with open(out_path, 'w', encoding='utf-8') as jf:
    json.dump(existing, jf, ensure_ascii=False, indent=2)

print(f"\nUpdated {out_path}")
