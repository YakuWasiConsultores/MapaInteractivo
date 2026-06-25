import geopandas as gpd
import matplotlib.pyplot as plt
import json

# Paths
shp_ecu = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\ORGANIZACION_TERRITORIAL_PROVINCIAL.shp"
corridor_json = r"H:\Yakuwarmi\mapas interactivos\corridor_polygon.json"

# Load corridor bbox from json
with open(corridor_json, 'r') as f:
    corr = json.load(f)
    c_south = corr['bbox']['south']
    c_north = corr['bbox']['north']
    c_west = corr['bbox']['west']
    c_east = corr['bbox']['east']

# Ecuador Inset
try:
    ecu = gpd.read_file(shp_ecu)
    if ecu.crs != "EPSG:4326":
        ecu = ecu.to_crs(epsg=4326)
    
    # Ecuador Inset (Map 1)
    fig, ax = plt.subplots(figsize=(10, 10), dpi=600)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    
    # Plot all Ecuador in light grey
    ecu.plot(ax=ax, color='#e0e0e0', edgecolor='#888888', linewidth=1.0)
    
    # Highlight Napo in Ecuador map (Map 2 location)
    napo = ecu[ecu['DPA_DESPRO'] == 'NAPO']
    if not napo.empty:
        napo.plot(ax=ax, color='#a9dfbf', edgecolor='#555555', linewidth=1.5) # Light green
    
    # Plot Corridor BBox (Map 3 location)
    ax.plot([(c_west+c_east)/2], [(c_south+c_north)/2], marker='o', color='red', markersize=15)
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(r"H:\Yakuwarmi\mapas interactivos\inset_ecuador.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    
    # Napo Inset (Map 2)
    fig, ax = plt.subplots(figsize=(10, 10), dpi=600)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    
    # Plot all Ecuador as background context, showing province borders clearly
    ecu.plot(ax=ax, color='#f5f5f5', edgecolor='#aaaaaa', linewidth=1.5)
    
    # Highlight Napo
    if not napo.empty:
        napo.plot(ax=ax, color='#d0d0d0', edgecolor='#333333', linewidth=3)
        
        # Zoom to Napo bounds with much more padding to see context
        minx, miny, maxx, maxy = napo.total_bounds
        pad_x = (maxx - minx) * 1.5
        pad_y = (maxy - miny) * 1.5
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
    
    # Plot Corridor BBox (Map 3 location)
    ax.plot([c_west, c_east, c_east, c_west, c_west], 
            [c_south, c_south, c_north, c_north, c_south], 
            color='red', linewidth=5, linestyle='dashed')
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(r"H:\Yakuwarmi\mapas interactivos\inset_napo.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("Insets generated.")
except Exception as e:
    print(f"Error generating insets: {e}")
