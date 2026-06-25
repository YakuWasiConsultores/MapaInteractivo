import json
from pathlib import Path

from yacuwarmi_map.cli import parse_args


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def test_community_ids_are_unique_and_complete():
    communities = json.loads((DATA / "communities_geo.json").read_text(encoding="utf-8"))
    ids = sorted(item["id"] for item in communities)
    assert ids == list(range(1, 26))


def test_inaturalist_snapshot_covers_all_communities():
    communities = json.loads((DATA / "communities_geo.json").read_text(encoding="utf-8"))
    data = json.loads((DATA / "inaturalist_data.json").read_text(encoding="utf-8"))
    assert {str(item["id"]) for item in communities} == set(data["community_species"])


def test_local_inaturalist_photos_exist():
    data = json.loads((DATA / "inaturalist_data.json").read_text(encoding="utf-8"))
    for community in data["community_species"].values():
        for list_name in ("all_species", "fauna_species", "flora_species"):
            for species in community.get(list_name, []):
                photo = species.get("photo_url", "")
                if photo and not photo.startswith(("http://", "https://")):
                    assert (ROOT / photo).is_file(), photo


def test_vendor_assets_exist():
    assert (ROOT / "assets/vendor/leaflet.css").is_file()
    assert (ROOT / "assets/vendor/leaflet.js").is_file()
    assert (ROOT / "assets/vendor/proj4.js").is_file()


def test_pdf_export_defaults_to_600_dpi():
    args = parse_args(["export-pdf"])
    assert args.dpi == 600
