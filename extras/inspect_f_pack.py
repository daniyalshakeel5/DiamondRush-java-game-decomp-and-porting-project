#!/usr/bin/env python3
import argparse,struct
from pathlib import Path

def inspect(path):
    b=Path(path).read_bytes(); n=b[0]; base=1+8*n
    print(f'{path}: {len(b)} bytes, {n} resources, header={base}')
    end=base
    for i in range(n):
        off,size=struct.unpack_from('<II',b,1+8*i); start=base+off; stop=start+size; end=max(end,stop)
        print(f'  {i:2d}: rel=0x{off:08x} size=0x{size:08x} file=[0x{start:x},0x{stop:x}) preview={b[start:start+12].hex(" ")}')
    print('  payload ends exactly:', end==len(b))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='+'); a=ap.parse_args()
    for p in a.files: inspect(p)
if __name__=='__main__': main()
