#!/usr/bin/env python3
import argparse, csv, json
from pathlib import Path
from PIL import Image

XOR_KEY=0x55
EMPTY=0xAA

def decode_file(path):
    b=Path(path).read_bytes()
    if len(b)<2: raise ValueError(f'{path}: too short')
    version,n=b[0],b[1]; pos=2; levels=[]
    for li in range(1,n+1):
        if pos+4>len(b): raise ValueError(f'{path}: truncated level header {li}')
        w=int.from_bytes(b[pos:pos+2],'little'); h=int.from_bytes(b[pos+2:pos+4],'little'); pos+=4
        layers=[]
        size=w*h
        for _ in range(3):
            raw=b[pos:pos+size]
            if len(raw)!=size: raise ValueError(f'{path}: truncated level {li}')
            layers.append([v^XOR_KEY for v in raw]); pos+=size
        levels.append({'level':li,'width':w,'height':h,'pixels':[w*24,h*24],'layers':layers})
    if pos!=len(b): raise ValueError(f'{path}: {len(b)-pos} trailing bytes')
    return version,levels

def debug_png(level,out):
    w,h=level['width'],level['height']; pix=[]
    for y in range(h):
        for x in range(w):
            v=level['layers'][0][y*w+x]
            pix.append(((v*53)%256,(v*97)%256,(v*193)%256))
    im=Image.new('RGB',(w,h)); im.putdata(pix); im.resize((w*24,h*24),Image.Resampling.NEAREST).save(out)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('-o','--output',default='decoded'); ap.add_argument('--debug-png',action='store_true'); a=ap.parse_args()
    root=Path(a.root); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    worlds={}
    for i in range(3):
        ver,lv=decode_file(root/f'w{i}.bin'); worlds[f'world{i+1}']=lv
        if a.debug_png:
            d=out/f'world{i+1}'; d.mkdir(exist_ok=True)
            for x in lv: debug_png(x,d/f'level_{x["level"]:02d}.png')
    (out/'levels.json').write_text(json.dumps(worlds,separators=(',',':')))
    detailed={'format':'diamond-rush-world-v1','xor_key':XOR_KEY,'empty_decoded':EMPTY,'worlds':worlds}
    (out/'levels_detailed.json').write_text(json.dumps(detailed,indent=2))
    with (out/'levels.csv').open('w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['world','level','width','height','pixel_width','pixel_height'])
        for wn,ls in worlds.items():
            for x in ls: wr.writerow([wn,x['level'],x['width'],x['height'],*x['pixels']])
    print('decoded',sum(len(v) for v in worlds.values()),'levels')
if __name__=='__main__': main()
