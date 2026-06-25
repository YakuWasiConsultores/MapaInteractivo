import struct
import json
import math

dbf_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.dbf"
shp_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.shp"
shx_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.shx"

# UTM Zone 18S (Central Meridian -75) to WGS84/SIRGAS2000
def utm_to_latlon(easting, northing, zone=18, southern=True):
    a = 6378137.0
    f = 1 / 298.257222101  # GRS 1980
    e = math.sqrt(2 * f - f * f)
    e2 = e * e / (1 - e * e)
    k0 = 0.9996
    
    x = easting - 500000.0
    y = northing
    if southern:
        y = y - 10000000.0
    
    M = y / k0
    mu = M / (a * (1 - e*e/4 - 3*e**4/64 - 5*e**6/256))
    
    e1 = (1 - math.sqrt(1 - e*e)) / (1 + math.sqrt(1 - e*e))
    
    phi1 = mu + (3*e1/2 - 27*e1**3/32) * math.sin(2*mu)
    phi1 += (21*e1**2/16 - 55*e1**4/32) * math.sin(4*mu)
    phi1 += (151*e1**3/96) * math.sin(6*mu)
    phi1 += (1097*e1**4/512) * math.sin(8*mu)
    
    N1 = a / math.sqrt(1 - e*e * math.sin(phi1)**2)
    T1 = math.tan(phi1)**2
    C1 = e2 * math.cos(phi1)**2
    R1 = a * (1 - e*e) / (1 - e*e * math.sin(phi1)**2)**1.5
    D = x / (N1 * k0)
    
    lat = phi1 - (N1 * math.tan(phi1) / R1) * (
        D**2/2 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e2) * D**4/24
        + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*e2 - 3*C1**2) * D**6/720
    )
    
    lon = (D - (1 + 2*T1 + C1) * D**3/6
           + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*e2 + 24*T1**2) * D**5/120) / math.cos(phi1)
    
    # Central meridian for zone 18: -75 degrees
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)  # = -75 for zone 18
    
    return math.degrees(lat), math.degrees(lon + lon0)

# Test with known coords: Archidona is approximately -0.91°, -77.8°
test_lat, test_lon = utm_to_latlon(200000, 9900000)
print(f"Test (200000, 9900000) -> lat={test_lat:.4f}, lon={test_lon:.4f}")

# DBF structure
HLEN = 385
RLEN = 507
fields = [
    ('fid', 'N', 20), ('id', 'N', 20), ('NAME FINAL', 'C', 100),
    ('ids', 'N', 20), ('NUM_ID', 'N', 10), ('FID_2', 'N', 11),
    ('Nombre', 'C', 30), ('Nombre_2', 'C', 254),
    ('Area', 'N', 19), ('Ha', 'N', 11), ('Ha_total', 'N', 11)
]

# Read SHX offsets
with open(shx_path, 'rb') as shx:
    shx.read(100)
    offsets = []
    while True:
        data = shx.read(8)
        if len(data) < 8:
            break
        offset = struct.unpack('>I', data[:4])[0] * 2
        length = struct.unpack('>I', data[4:])[0] * 2
        offsets.append((offset, length))

# Read each community with full polygon geometry
communities = []
with open(dbf_path, 'rb') as dbf, open(shp_path, 'rb') as shp:
    for idx in range(25):
        # DBF record
        dbf.seek(HLEN + idx * RLEN)
        rec = dbf.read(RLEN)
        vals = {}
        off = 1
        for nm, ft, fl in fields:
            v = rec[off:off+fl].decode('utf-8', errors='replace').strip()
            vals[nm] = v
            off += fl
        
        # SHP geometry
        offset, length = offsets[idx]
        shp.seek(offset + 8)
        st = struct.unpack('<I', shp.read(4))[0]
        bx1 = struct.unpack('<d', shp.read(8))[0]
        by1 = struct.unpack('<d', shp.read(8))[0]
        bx2 = struct.unpack('<d', shp.read(8))[0]
        by2 = struct.unpack('<d', shp.read(8))[0]
        
        num_parts = struct.unpack('<I', shp.read(4))[0]
        num_points = struct.unpack('<I', shp.read(4))[0]
        
        parts = []
        for p in range(num_parts):
            parts.append(struct.unpack('<I', shp.read(4))[0])
        
        points_utm = []
        for pt in range(num_points):
            px = struct.unpack('<d', shp.read(8))[0]
            py = struct.unpack('<d', shp.read(8))[0]
            points_utm.append((px, py))
        
        # Convert to lat/lon
        points_ll = []
        for px, py in points_utm:
            plat, plon = utm_to_latlon(px, py)
            points_ll.append([plon, plat])
        
        # Split into rings by parts
        rings = []
        for i, start in enumerate(parts):
            end = parts[i+1] if i+1 < len(parts) else num_points
            ring = points_ll[start:end]
            rings.append(ring)
        
        # Centroid
        cx = sum(p[0] for p in points_ll) / len(points_ll)
        cy = sum(p[1] for p in points_ll) / len(points_ll)
        
        # Bbox in WGS84
        lat_s, lon_w = utm_to_latlon(bx1, by1)
        lat_n, lon_e = utm_to_latlon(bx2, by2)
        
        name = vals['NAME FINAL']
        ha = vals['Ha']
        
        comm = {
            'id': idx + 1,
            'name': name,
            'ha': ha,
            'bbox_wgs84': {
                'south': min(lat_s, lat_n),
                'north': max(lat_s, lat_n),
                'west': min(lon_w, lon_e),
                'east': max(lon_w, lon_e)
            },
            'centroid': [cx, cy],
            'rings': rings
        }
        communities.append(comm)
        print(f"[{idx+1}] {name} | {ha} ha | Center: ({cy:.4f}, {cx:.4f})")

# Save
out_path = r"H:\Yakuwarmi\mapas interactivos\communities_geo.json"
with open(out_path, 'w', encoding='utf-8') as jf:
    json.dump(communities, jf, ensure_ascii=False, indent=2)
print(f"\nSaved {len(communities)} communities to {out_path}")

# Global bbox
all_lats = [c['bbox_wgs84']['south'] for c in communities] + [c['bbox_wgs84']['north'] for c in communities]
all_lons = [c['bbox_wgs84']['west'] for c in communities] + [c['bbox_wgs84']['east'] for c in communities]
print(f"\nGlobal bounds (WGS84):")
print(f"  South: {min(all_lats):.4f}, North: {max(all_lats):.4f}")
print(f"  West: {min(all_lons):.4f}, East: {max(all_lons):.4f}")
