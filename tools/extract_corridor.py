import struct
import json
import math

shp_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Poligono_Corredor.shp"
shx_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Poligono_Corredor.shx"

def utm17s_to_latlon(easting, northing):
    a = 6378137.0
    f = 1 / 298.257223563
    e = math.sqrt(2 * f - f * f)
    e2 = e * e / (1 - e * e)
    k0 = 0.9996
    x = easting - 500000.0
    y = northing - 10000000.0
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
        + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*e2 - 3*C1**2) * D**6/720)
    lon = (D - (1 + 2*T1 + C1) * D**3/6
           + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*e2 + 24*T1**2) * D**5/120) / math.cos(phi1)
    lon0 = math.radians(-81.0)
    return math.degrees(lat), math.degrees(lon + lon0)

# Read SHX
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

print(f"Corredor polygon: {len(offsets)} records")

# Read SHP
with open(shp_path, 'rb') as shp:
    for idx, (offset, length) in enumerate(offsets):
        shp.seek(offset + 8)
        st = struct.unpack('<I', shp.read(4))[0]
        bx1 = struct.unpack('<d', shp.read(8))[0]
        by1 = struct.unpack('<d', shp.read(8))[0]
        bx2 = struct.unpack('<d', shp.read(8))[0]
        by2 = struct.unpack('<d', shp.read(8))[0]
        
        num_parts = struct.unpack('<I', shp.read(4))[0]
        num_points = struct.unpack('<I', shp.read(4))[0]
        print(f"  Record {idx}: type={st}, parts={num_parts}, points={num_points}")
        
        parts = [struct.unpack('<I', shp.read(4))[0] for _ in range(num_parts)]
        
        points = []
        for _ in range(num_points):
            px = struct.unpack('<d', shp.read(8))[0]
            py = struct.unpack('<d', shp.read(8))[0]
            lat, lon = utm17s_to_latlon(px, py)
            points.append([lon, lat])
        
        # Split into rings
        rings = []
        for i, start in enumerate(parts):
            end = parts[i+1] if i+1 < len(parts) else num_points
            rings.append(points[start:end])
        
        # Simplify - take every Nth point to reduce size
        simplified_rings = []
        for ring in rings:
            n = max(1, len(ring) // 500)  # max ~500 points per ring
            simplified = ring[::n]
            if simplified[-1] != ring[-1]:
                simplified.append(ring[-1])
            simplified_rings.append(simplified)
            print(f"    Ring: {len(ring)} pts -> {len(simplified)} simplified")
        
        corridor_data = {
            'bbox': {
                'south': min(p[1] for r in simplified_rings for p in r),
                'north': max(p[1] for r in simplified_rings for p in r),
                'west': min(p[0] for r in simplified_rings for p in r),
                'east': max(p[0] for r in simplified_rings for p in r)
            },
            'rings': simplified_rings
        }

out_path = r"H:\Yakuwarmi\mapas interactivos\corridor_polygon.json"
with open(out_path, 'w', encoding='utf-8') as jf:
    json.dump(corridor_data, jf, indent=2)
print(f"\nSaved corridor polygon to {out_path}")
print(f"BBox: {corridor_data['bbox']}")
