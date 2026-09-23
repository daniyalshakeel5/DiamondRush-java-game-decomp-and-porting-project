"""Diamond Rush level (wN.bin) loader + first-pass static renderer."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gl_sprite import *
from PIL import Image, ImageDraw

TILE = 24

def load_world(path):
    d = open(path, 'rb').read()
    (n,) = struct.unpack('<I', d[:4]); p = d[4:4+n]
    nl = p[1]; pos = 2; levels = []
    for _ in range(nl):
        w, h = struct.unpack('<HH', p[pos:pos+4]); pos += 4
        layers = [list(p[pos+k*w*h:pos+(k+1)*w*h]) for k in range(3)]; pos += 3*w*h
        levels.append(dict(w=w, h=h, layers=layers))
    assert pos == len(p)
    return levels

def module_image(spr, i, pal=0):
    w, h = spr.sizes[i]
    px = spr.module_pixels(i, pal)
    im = Image.new('RGBA', (w, h))
    im.putdata([((c>>16)&255, (c>>8)&255, c&255, (c>>24)&255) for c in px])
    return im

def s8(v): return v - 256 if v > 127 else v

def draw_frame(spr, frame, canvas, X, Y, flags=0, pal=0, cache={}):
    start, cnt = spr.frame_start[frame], spr.frame_count[frame]
    for k in range(cnt):
        e = spr.fm[(start+k)*4:(start+k)*4+4]
        mod, mx, my, mf = e[0], s8(e[1]), s8(e[2]), e[3]
        if len(spr.sizes) > 256: mod |= (mf & 0xC0) << 2
        x = X - mx if flags & 1 else X + mx
        y = Y - my if flags & 2 else Y + my
        w, h = spr.sizes[mod]
        if w <= 0 or h <= 0: continue
        key = (id(spr), mod, pal)
        if key not in cache: cache[key] = module_image(spr, mod, pal)
        im = cache[key]
        f = flags ^ (mf & 3)
        if f & 1: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if f & 2: im = im.transpose(Image.FLIP_TOP_BOTTOM)
        if flags & 1: x -= w
        if flags & 2: y -= h
        canvas.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else canvas.paste(im, (x, y), im)

def render_level(world_idx, level_idx, out):
    lv = load_world(f'x/w{world_idx}.bin')[level_idx]
    chunks = read_container(open(f'x/{world_idx}.f', 'rb').read())
    tiles = parse_sprite(chunks[2])          # terrain frames
    floor = module_image(parse_sprite(chunks[3]), 0)
    W, H = lv['w'], lv['h']
    im = Image.new('RGBA', (W*TILE, H*TILE), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    base = lv['layers'][0]
    for y in range(H):
        for x in range(W):
            v = base[x + y*W]
            px, py = x*TILE, y*TILE
            if v < 80 or v > 127:
                im.alpha_composite(floor, (px, py))
            if 80 <= v < 80 + len(tiles.frame_count):
                draw_frame(tiles, v - 80, im, px, py)
            elif v < 80:
                d.rectangle([px+3, py+3, px+TILE-4, py+TILE-4], outline=(255, 60, 60, 255))
                d.text((px+5, py+6), str(v), fill=(255, 255, 0, 255))
    im.convert('RGB').save(out)
    return im.size

if __name__ == '__main__':
    os.makedirs('out/levels', exist_ok=True)
    print(render_level(0, 0, 'out/levels/w0_l0.png'))
