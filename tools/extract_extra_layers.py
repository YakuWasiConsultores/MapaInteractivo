import geopandas as gpd
import json
import math

def utm18s_to_latlon(gdf):
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=31988) # Assume SIRGAS 2000 UTM 18S or similar for communities
    return gdf.to_crs(epsg=4326)

def utm17s_to_latlon(gdf):
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=32717) # Assume WGS 84 UTM 17S
    return gdf.to_crs(epsg=4326)

files = [
    {
        "name": "Posibles_comunidades",
        "path": r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Posibles_comunidades_a_integrar.shp",
        "crs": 31988 # SIRGAS 2000 UTM 18S for communities
    },
    {
        "name": "SNAP",
        "path": r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Actualizacion_SNAP.shp",
        "crs": 32717 # Usually UTM 17S or national crs for SNAP, let's read its crs
    },
    {
        "name": "KBA",
        "path": r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Ecu_52_kba.shp",
        "crs": None # Read from file
    }
]

for f in files:
    try:
        gdf = gpd.read_file(f["path"])
        if gdf.crs is None and f["crs"] is not None:
            gdf = gdf.set_crs(epsg=f["crs"])
        
        # Reproject to WGS84
        gdf = gdf.to_crs(epsg=4326)
        
        # Simplify geometry for web viewing
        gdf["geometry"] = gdf["geometry"].simplify(0.001)
        
        out_path = rf"H:\Yakuwarmi\mapas interactivos\{f['name']}.geojson"
        gdf.to_file(out_path, driver="GeoJSON")
        print(f"Exported {f['name']} successfully.")
    except Exception as e:
        print(f"Error processing {f['name']}: {e}")
