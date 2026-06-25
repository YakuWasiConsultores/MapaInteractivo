import struct
import json

dbf_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.dbf"
shp_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.shp"
shx_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.shx"

# 1. Read DBF header and fields
with open(dbf_path, 'rb') as f:
    f.read(1)  # version
    nrec = struct.unpack('<I', f.read(4))[0]
    hlen = struct.unpack('<H', f.read(2))[0]
    rlen = struct.unpack('<H', f.read(2))[0]
    print(f"DBF: {nrec} records, header={hlen}, reclen={rlen}")
    
    f.seek(32)
    fields = []
    while True:
        b = f.read(32)
        if b[0] == 13:
            break
        name = b[:11].replace(b'\x00', b'').decode('latin1')
        ftype = chr(b[11])
        flen = b[16]
        fdec = b[17]
        fields.append((name, ftype, flen, fdec))
    
    print("Fields:", [n for n, t, l, d in fields])

# 2. Read SHX to get offsets
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

print(f"SHX: {len(offsets)} records")

# 3. Read SHP header for global bbox
with open(shp_path, 'rb') as shp:
    shp.read(36)  # file code + unused + file length + version + shape type
    xmin_g = struct.unpack('<d', shp.read(8))[0]
    ymin_g = struct.unpack('<d', shp.read(8))[0]
    xmax_g = struct.unpack('<d', shp.read(8))[0]
    ymax_g = struct.unpack('<d', shp.read(8))[0]
    print(f"Global BBox: W={xmin_g:.4f}, S={ymin_g:.4f}, E={xmax_g:.4f}, N={ymax_g:.4f}")

# 4. For each record, read DBF name + SHP bbox
communities = []
with open(dbf_path, 'rb') as dbf, open(shp_path, 'rb') as shp:
    for idx in range(min(nrec, len(offsets))):
        # Read DBF record
        dbf.seek(hlen + idx * rlen)
        rec = dbf.read(rlen)
        vals = {}
        off = 1
        for nm, ft, fl, fd in fields:
            v = rec[off:off+fl].decode('latin1', errors='replace').strip()
            vals[nm] = v
            off += fl
        
        name = vals.get('NAME FINAL', '').strip()
        if not name:
            continue
        
        # Read SHP bbox
        offset, length = offsets[idx]
        shp.seek(offset + 8)  # skip record number and content length
        st = struct.unpack('<I', shp.read(4))[0]
        if st == 0:
            continue
        bx1 = struct.unpack('<d', shp.read(8))[0]
        by1 = struct.unpack('<d', shp.read(8))[0]
        bx2 = struct.unpack('<d', shp.read(8))[0]
        by2 = struct.unpack('<d', shp.read(8))[0]
        
        num_parts = struct.unpack('<I', shp.read(4))[0]
        num_points = struct.unpack('<I', shp.read(4))[0]
        
        communities.append({
            'id': vals.get('NUM_ID', str(idx+1)),
            'name': name,
            'area': vals.get('Area', ''),
            'ha': vals.get('Ha', ''),
            'bbox': [bx1, by1, bx2, by2],
            'num_points': num_points
        })

print(f"\nFound {len(communities)} communities with data:")
for c in communities:
    print(f"  [{c['id']}] {c['name']} | Area: {c['area']} | BBox: W={c['bbox'][0]:.4f} S={c['bbox'][1]:.4f} E={c['bbox'][2]:.4f} N={c['bbox'][3]:.4f}")

# Save to JSON
out_path = r"H:\Yakuwarmi\mapas interactivos\communities.json"
with open(out_path, 'w', encoding='utf-8') as jf:
    json.dump(communities, jf, ensure_ascii=False, indent=2)
print(f"\nSaved to {out_path}")
