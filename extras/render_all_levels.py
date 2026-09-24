import argparse, struct
from pathlib import Path
from render_dr import render

def main():
    ap=argparse.ArgumentParser(description='Render all 41 Diamond Rush levels.')
    ap.add_argument('root',help='extracted game directory containing w0.bin/w1.bin/w2.bin and .f assets')
    ap.add_argument('-o','--output',default='diamond_rush_levels_rendered')
    a=ap.parse_args(); root=Path(a.root); out=Path(a.output); count=0
    for w in range(3):
        b=(root/f'w{w}.bin').read_bytes(); n=b[1]; pos=2
        wd=out/f'world{w+1}'; wd.mkdir(parents=True,exist_ok=True)
        for level in range(1,n+1):
            W,H=struct.unpack_from('<HH',b,pos); pos += 4 + 3*W*H
            target=wd/f'level_{level:02d}.png'
            render(root,w,level-1,target); count += 1
    print(f'generated {count} levels in {out}')
if __name__=='__main__': main()
