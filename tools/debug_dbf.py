import struct
import json

dbf_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.dbf"
shp_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.shp"
shx_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.shx"

# Debug: Read raw DBF header bytes
with open(dbf_path, 'rb') as f:
    header_raw = f.read(32)
    print("First 32 bytes (hex):", header_raw.hex())
    print("Byte 0 (version):", header_raw[0])
    print("Bytes 1-3 (date):", header_raw[1], header_raw[2], header_raw[3])
    
    nrec = struct.unpack('<I', header_raw[4:8])[0]
    hlen = struct.unpack('<H', header_raw[8:10])[0]
    rlen = struct.unpack('<H', header_raw[10:12])[0]
    print(f"Num records: {nrec}")
    print(f"Header length: {hlen}")
    print(f"Record length: {rlen}")
    
    # Read field descriptors
    f.seek(32)
    fields = []
    for i in range(50):  # max 50 fields
        b = f.read(32)
        if len(b) < 32 or b[0] == 0x0D:
            break
        name = b[:11].split(b'\x00')[0].decode('latin1')
        ftype = chr(b[11])
        flen = b[16]
        fdec = b[17]
        fields.append((name, ftype, flen, fdec))
        print(f"  Field {i}: name='{name}' type={ftype} len={flen} dec={fdec}")
    
    print(f"\nTotal fields: {len(fields)}")
    
    # Calculate expected header length
    expected_hlen = 32 + len(fields) * 32 + 1  # +1 for terminator
    print(f"Expected header length: {expected_hlen}")
    print(f"Actual header length from file: {hlen}")
    
    # Use expected header length if actual is wrong
    actual_hlen = hlen if hlen > 0 else expected_hlen
    
    # Calculate expected record length
    expected_rlen = 1 + sum(fl for _, _, fl, _ in fields)  # +1 for deletion flag
    print(f"Expected record length: {expected_rlen}")
    print(f"Actual record length from file: {rlen}")
    
    actual_rlen = rlen if rlen > 0 else expected_rlen
    
    # Read first 30 records
    f.seek(actual_hlen)
    print(f"\n=== FIRST 30 RECORDS ===")
    valid_records = []
    for r in range(min(30, nrec)):
        rec = f.read(actual_rlen)
        if len(rec) < actual_rlen:
            break
        vals = {}
        offset = 1  # skip deletion flag
        for nm, ft, fl, fd in fields:
            v = rec[offset:offset+fl].decode('utf-8', errors='replace').strip()
            vals[nm] = v
            offset += fl
        name = vals.get('NAME FINAL', '').strip()
        if name and not '\x00' in name:
            valid_records.append((r, vals))
            print(f"  [{r}] {name} | Area: {vals.get('Area', '')} | Ha: {vals.get('Ha', '')}")
    
    print(f"\nValid records found: {len(valid_records)}")

# Also try reading file size to compute actual record count
file_size = __import__('os').path.getsize(dbf_path)
print(f"\nDBF file size: {file_size} bytes")
actual_nrec = (file_size - actual_hlen) // actual_rlen
print(f"Computed record count: {actual_nrec}")
