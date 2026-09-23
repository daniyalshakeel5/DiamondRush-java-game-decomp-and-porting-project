import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
from gl_sprite import *
from PIL import Image

def sheet(spr, pal=0, cols=16, scale=2, bg=(60,60,80)):
    n = len(spr.sizes)
    if n == 0: return None
    cw = max(w for w,h in spr.sizes)+2; ch = max(h for w,h in spr.sizes)+2
    rows = (n+cols-1)//cols
    im = Image.new('RGBA', (cols*cw, rows*ch), bg+(255,))
    for i,(w,h) in enumerate(spr.sizes):
        if w<=0 or h<=0: continue
        px = spr.module_pixels(i, pal)
        t = Image.new('RGBA', (w,h))
        t.putdata([((c>>16)&255,(c>>8)&255,c&255,(c>>24)&255) for c in px])
        im.alpha_composite(t, ((i%cols)*cw+1, (i//cols)*ch+1))
    return im.resize((im.width*scale, im.height*scale), Image.NEAREST)

if __name__ == '__main__':
    out = 'out/sheets'; os.makedirs(out, exist_ok=True)
    for f in sorted(glob.glob('x/*.f')+['x/demoSpr.bin']):
        name = os.path.basename(f).split('.')[0]
        try: chunks = read_container(open(f,'rb').read())
        except Exception: continue
        for i,c in enumerate(chunks):
            if c[:2] != bytes([0xdf,0x03]): continue
            s = parse_sprite(c)
            im = sheet(s)
            if im: im.save(f'{out}/{name}_{i}.png')
    print(len(os.listdir(out)), 'sheets')
