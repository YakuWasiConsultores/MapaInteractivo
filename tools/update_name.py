import json

# Update communities_geo.json
with open(r"H:\Yakuwarmi\mapas interactivos\communities_geo.json", "r", encoding="utf-8") as f:
    communities = json.load(f)

for c in communities:
    if c["id"] == 6:
        c["name"] = "COMUNIDAD KICHWA CHALLUAYAKU"
        break

with open(r"H:\Yakuwarmi\mapas interactivos\communities_geo.json", "w", encoding="utf-8") as f:
    json.dump(communities, f, ensure_ascii=False, indent=2)

# Update inaturalist_data.json
with open(r"H:\Yakuwarmi\mapas interactivos\inaturalist_data.json", "r", encoding="utf-8") as f:
    inat = json.load(f)

if "6" in inat["community_species"]:
    inat["community_species"]["6"]["name"] = "COMUNIDAD KICHWA CHALLUAYAKU"

with open(r"H:\Yakuwarmi\mapas interactivos\inaturalist_data.json", "w", encoding="utf-8") as f:
    json.dump(inat, f, ensure_ascii=False, indent=2)
