import geopandas as gpd
import json
import os

files = [
    {
        "name": "Ecu_25",
        "path": r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Ecu_25.shp",
    },
    {
        "name": "Corredor_NorOriental",
        "path": r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Corredor_NorOriental.shp",
    },
    {
        "name": "Napo",
        "path": r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Napo.shp",
    }
]

for f in files:
    try:
        if not os.path.exists(f["path"]):
            print(f"File not found: {f['path']}")
            continue
            
        gdf = gpd.read_file(f["path"])
        
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=32717) # Assume UTM 17S WGS84 for Napo/Ecu if missing
            
        # Reproject to WGS84
        gdf = gdf.to_crs(epsg=4326)
        
        # Simplify geometry heavily for Napo and Ecu to keep HTML small
        gdf["geometry"] = gdf["geometry"].simplify(0.005)
        
        out_path = rf"H:\Yakuwarmi\mapas interactivos\{f['name']}.geojson"
        gdf.to_file(out_path, driver="GeoJSON")
        print(f"Exported {f['name']} successfully.")
    except Exception as e:
        print(f"Error processing {f['name']}: {e}")
