"""
Query iNaturalist API for representative species in the corridor area.
Uses the global bounding box of all 25 communities.
"""
import json
import urllib.request
import urllib.parse
import time

# Load community data
with open(r"H:\Yakuwarmi\mapas interactivos\communities_geo.json", 'r', encoding='utf-8') as f:
    communities = json.load(f)

# Global bounding box
all_lats = []
all_lons = []
for c in communities:
    all_lats.extend([c['bbox_wgs84']['south'], c['bbox_wgs84']['north']])
    all_lons.extend([c['bbox_wgs84']['west'], c['bbox_wgs84']['east']])

swlat = min(all_lats)
swlng = min(all_lons)
nelat = max(all_lats)
nelng = max(all_lons)

print(f"Querying iNaturalist for area: ({swlat:.4f},{swlng:.4f}) to ({nelat:.4f},{nelng:.4f})")

# Query iNaturalist species observations
# We want research-grade observations of animals and plants
base_url = "https://api.inaturalist.org/v1/observations/species_counts"

results_by_community = {}

# First, get the overall top species for the entire corridor
params = {
    'swlat': f'{swlat:.4f}',
    'swlng': f'{swlng:.4f}',
    'nelat': f'{nelat:.4f}',
    'nelng': f'{nelng:.4f}',
    'quality_grade': 'research',
    'per_page': '50',
    'order': 'desc',
    'order_by': 'count',
    'locale': 'es'
}

url = base_url + "?" + urllib.parse.urlencode(params)
print(f"\nQuerying: {url}")

req = urllib.request.Request(url, headers={'User-Agent': 'Yakuwarmi-Corredor/1.0'})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

print(f"Total species found: {data.get('total_results', 0)}")
print("\n=== TOP 50 SPECIES (ENTIRE CORRIDOR) ===")

global_species = []
for r in data.get('results', []):
    taxon = r.get('taxon', {})
    count = r.get('count', 0)
    name = taxon.get('name', '')
    common = taxon.get('preferred_common_name', '')
    rank = taxon.get('rank', '')
    iconic = taxon.get('iconic_taxon_name', '')
    photo_url = ''
    if taxon.get('default_photo'):
        photo_url = taxon['default_photo'].get('medium_url', '')
    
    species_data = {
        'taxon_id': taxon.get('id'),
        'name': name,
        'common_name': common,
        'rank': rank,
        'iconic_group': iconic,
        'count': count,
        'photo_url': photo_url
    }
    global_species.append(species_data)
    print(f"  {count:4d}x {name} ({common}) [{iconic}]")

# Now query per community for the most interesting ones (animals & iconic species)
print("\n\n=== QUERYING PER COMMUNITY ===")
for comm in communities:
    bbox = comm['bbox_wgs84']
    comm_name = comm['name']
    
    params_comm = {
        'swlat': f"{bbox['south']:.4f}",
        'swlng': f"{bbox['west']:.4f}",
        'nelat': f"{bbox['north']:.4f}",
        'nelng': f"{bbox['east']:.4f}",
        'quality_grade': 'research',
        'per_page': '10',
        'order': 'desc',
        'order_by': 'count',
        'iconic_taxa[]': 'Mammalia,Aves,Reptilia,Amphibia',
        'locale': 'es'
    }
    
    url_comm = base_url + "?" + urllib.parse.urlencode(params_comm, doseq=True)
    
    try:
        req_comm = urllib.request.Request(url_comm, headers={'User-Agent': 'Yakuwarmi-Corredor/1.0'})
        with urllib.request.urlopen(req_comm, timeout=30) as resp_comm:
            data_comm = json.loads(resp_comm.read().decode())
        
        species_list = []
        for r in data_comm.get('results', []):
            taxon = r.get('taxon', {})
            count = r.get('count', 0)
            photo_url = ''
            if taxon.get('default_photo'):
                photo_url = taxon['default_photo'].get('medium_url', '')
            
            species_list.append({
                'taxon_id': taxon.get('id'),
                'name': taxon.get('name', ''),
                'common_name': taxon.get('preferred_common_name', ''),
                'rank': taxon.get('rank', ''),
                'iconic_group': taxon.get('iconic_taxon_name', ''),
                'count': count,
                'photo_url': photo_url
            })
        
        results_by_community[comm['id']] = {
            'name': comm_name,
            'total': data_comm.get('total_results', 0),
            'species': species_list
        }
        
        top = species_list[0] if species_list else None
        if top:
            print(f"  [{comm['id']}] {comm_name}: {data_comm.get('total_results', 0)} species - Top: {top['name']} ({top['common_name']})")
        else:
            print(f"  [{comm['id']}] {comm_name}: No animal observations found")
        
    except Exception as e:
        print(f"  [{comm['id']}] {comm_name}: Error - {e}")
        results_by_community[comm['id']] = {'name': comm_name, 'total': 0, 'species': []}
    
    time.sleep(0.5)  # Rate limiting

# Save all results
output = {
    'global_species': global_species,
    'community_species': results_by_community,
    'corridor_bbox': {
        'south': swlat,
        'north': nelat,
        'west': swlng,
        'east': nelng
    }
}

out_path = r"H:\Yakuwarmi\mapas interactivos\inaturalist_data.json"
with open(out_path, 'w', encoding='utf-8') as jf:
    json.dump(output, jf, ensure_ascii=False, indent=2)

print(f"\nSaved iNaturalist data to {out_path}")
