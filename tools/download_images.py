import json
import os
import urllib.request
from urllib.parse import urlparse
import shutil

base_dir = r'H:\Yakuwarmi\mapas interactivos'
assets_dir = os.path.join(base_dir, 'assets', 'images')
os.makedirs(assets_dir, exist_ok=True)

# 1. Copy Logos
logos_dir = r'H:\Yakuwarmi\ACUS\LOGOS'
for f in os.listdir(logos_dir):
    src = os.path.join(logos_dir, f)
    dst = os.path.join(assets_dir, f)
    if os.path.isfile(src):
        shutil.copy2(src, dst)

# 2. Download iNat images and update JSON
inat_file = os.path.join(base_dir, 'inaturalist_data.json')
with open(inat_file, 'r', encoding='utf-8') as f:
    inat_data = json.load(f)

for cid, comm in inat_data['community_species'].items():
    for sp_list in ['fauna_species', 'flora_species']:
        for sp in comm.get(sp_list, []):
            url = sp.get('photo_url')
            if url and url.startswith('http'):
                filename = os.path.basename(urlparse(url).path)
                safe_name = f"inat_{cid}_{sp.get('id', '')}_{filename}"
                local_path = os.path.join(assets_dir, safe_name)
                if not os.path.exists(local_path):
                    try:
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                        print(f'Downloaded {safe_name}')
                    except Exception as e:
                        print(f'Error downloading {url}: {e}')
                # Update URL in JSON to be relative
                sp['photo_url'] = f'assets/images/{safe_name}'

with open(inat_file, 'w', encoding='utf-8') as f:
    json.dump(inat_data, f, ensure_ascii=False, indent=2)

print('Done downloading and copying images.')
