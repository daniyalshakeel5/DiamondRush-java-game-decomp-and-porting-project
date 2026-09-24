#!/usr/bin/env python3
import argparse, json
from pathlib import Path
XOR_KEY=0x55

def enc(levels):
    out=bytearray([1,len(levels)])
    for lev in levels:
        w,h=lev['width'],lev['height']; out += int(w).to_bytes(2,'little')+int(h).to_bytes(2,'little')
        for layer in lev['layers']:
            if len(layer)!=w*h: raise ValueError('layer length mismatch')
            out += bytes((int(v)^XOR_KEY)&255 for v in layer)
    return bytes(out)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('json'); ap.add_argument('-o','--output',default='rebuilt'); a=ap.parse_args()
    data=json.loads(Path(a.json).read_text()); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    for i in range(3):
        key=f'world{i+1}'; b=enc(data[key]); (out/f'w{i}.bin').write_bytes(b); print(key,len(b),'bytes')
if __name__=='__main__': main()
