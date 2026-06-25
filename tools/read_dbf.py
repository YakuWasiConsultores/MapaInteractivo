import struct
import os

dbf_path = r"H:\Yakuwarmi\Corredor_de_conectividad_8 (1)\SHP\Comunidades_del_corredor-25.dbf"

with open(dbf_path, 'rb') as f:
    ver = struct.unpack('B', f.read(1))[0]
    nrec = struct.unpack('<I', f.read(4))[0]
    hlen = struct.unpack('<H', f.read(2))[0]
    rlen = struct.unpack('<H', f.read(2))[0]
    print(f"Records: {nrec}, Header: {hlen}, RecLen: {rlen}")
    
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
    
    print("Fields:", fields)
    
    f.seek(hlen)
    for r in range(nrec):
        rec = f.read(rlen)
        vals = {}
        offset = 1
        for nm, ft, fl, fd in fields:
            v = rec[offset:offset+fl].decode('latin1', errors='replace').strip()
            vals[nm] = v
            offset += fl
        print(vals)
