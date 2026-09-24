import argparse
import struct
from pathlib import Path
from PIL import Image

TILE = 24
ENC_RLE_A, ENC_4BPP, ENC_2BPP, ENC_1BPP, ENC_8BPP, ENC_RLE_B = 10225, 5632, 1024, 512, 22018, 22258
PAL_ARGB8888, PAL_ARGB4444, PAL_ARGB1555, PAL_RGB565 = 0x8888, 0x4444, 0x5515, 0x6505

def u16(b, p): return b[p] | (b[p+1] << 8)

def read_container(data):
    n = data[0]
    base = 1 + 8*n
    out = []
    for i in range(n):
        off, size = struct.unpack_from('<II', data, 1 + 8*i)
        out.append(data[base+off:base+off+size])
    return out

class Sprite:
    def __init__(self, sizes, fm, fc, fs):
        self.sizes, self.fm, self.frame_count, self.frame_start = sizes, fm, fc, fs
        self.palettes, self.encoding, self.mod_data = [], 0, []

    def module_pixels(self, i, pal=0):
        w, h = self.sizes[i]; b = self.mod_data[i]; colors = self.palettes[pal]
        out, p, n = [], 0, w*h
        if self.encoding == ENC_RLE_A:
            while len(out) < n:
                v=b[p]; p+=1
                if v > 127: c=colors[b[p]]; p+=1; out += [c]*(v-128)
                else: out.append(colors[v])
        elif self.encoding == ENC_4BPP:
            while len(out) < n:
                v=b[p]; p+=1; out += [colors[v>>4], colors[v&15]]
        elif self.encoding == ENC_2BPP:
            while len(out) < n:
                v=b[p]; p+=1; out += [colors[(v>>s)&3] for s in (6,4,2,0)]
        elif self.encoding == ENC_1BPP:
            while len(out) < n:
                v=b[p]; p+=1; out += [colors[(v>>s)&1] for s in range(7,-1,-1)]
        elif self.encoding == ENC_8BPP:
            out = [colors[x] for x in b[:n]]
        elif self.encoding == ENC_RLE_B:
            while len(out) < n:
                v=b[p]; p+=1
                if v > 127:
                    for _ in range(v-128): out.append(colors[b[p]]); p+=1
                else:
                    c=colors[b[p]]; p+=1; out += [c]*v
        return out[:n]

def parse_sprite(b):
    p=6; nmod=u16(b,p); p+=2
    sizes=[(b[p+2*i], b[p+2*i+1]) for i in range(nmod)]; p+=2*nmod
    s=u16(b,p); p+=2; fm=b[p:p+s*4]; p+=4*s
    nfr=u16(b,p); p+=2; fc=[]; fs=[]
    for _ in range(nfr): fc.append(b[p]); fs.append(u16(b,p+2)); p+=4
    p += 4*nfr
    nan=u16(b,p); p+=2+5*nan
    nanim=u16(b,p); p+=2; p += 4*nanim
    spr=Sprite(sizes,fm,fc,fs)
    fmt=u16(b,p); p+=2; npal=b[p]; ncol=b[p+1]; p+=2
    for _ in range(npal):
        pal=[]
        for _ in range(ncol):
            if fmt == PAL_ARGB8888:
                v=int.from_bytes(b[p:p+4], 'little'); p+=4
            else:
                v16=u16(b,p); p+=2
                if fmt == PAL_ARGB4444:
                    a=(v16>>12)&15; r=(v16>>8)&15; g=(v16>>4)&15; bl=v16&15
                    v=(a*17<<24)|(r*17<<16)|(g*17<<8)|bl*17
                elif fmt == PAL_ARGB1555:
                    a=0xFF000000 if v16&0x8000 else 0
                    v=a|((v16&0x7c00)<<9)|((v16&0x3e0)<<6)|((v16&0x1f)<<3)
                elif fmt == PAL_RGB565:
                    a=0 if v16==0xf81f else 0xff000000
                    v=a|((v16&0xf800)<<8)|((v16&0x7e0)<<5)|((v16&0x1f)<<3)
                else: raise ValueError(f'unknown palette format {fmt:#x}')
            pal.append(v)
        spr.palettes.append(pal)
    spr.encoding=u16(b,p); p+=2
    for _ in range(nmod):
        n=u16(b,p); p+=2; spr.mod_data.append(b[p:p+n]); p+=n
    return spr

def module(spr, i):
    w,h=spr.sizes[i]
    px=spr.module_pixels(i)
    im=Image.new('RGBA',(w,h))
    im.putdata([((c>>16)&255,(c>>8)&255,c&255,(c>>24)&255) for c in px])
    return im

def frame(spr, fr):
    st,cnt=spr.frame_start[fr],spr.frame_count[fr]; parts=[]
    def s8(v): return v-256 if v>127 else v
    for k in range(cnt):
        mod,mx,my,mf=spr.fm[(st+k)*4:(st+k)*4+4]
        mx,my=s8(mx),s8(my)
        if mod >= len(spr.sizes): continue
        w,h=spr.sizes[mod]
        if w and h: parts.append((mod,mx,my,mf,w,h))
    if not parts: return None,(0,0)
    x0=min(p[1] for p in parts); y0=min(p[2] for p in parts)
    x1=max(p[1]+p[4] for p in parts); y1=max(p[2]+p[5] for p in parts)
    im=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
    for mod,mx,my,mf,w,h in parts:
        t=module(spr,mod)
        if mf&1: t=t.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if mf&2: t=t.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        im.alpha_composite(t,(mx-x0,my-y0))
    return im,(x0,y0)

class Assets:
    def __init__(self, root): self.root=Path(root); self.containers={}; self.sprites={}; self.modules={}; self.frames={}
    def chunks(self,name):
        if name not in self.containers: self.containers[name]=read_container((self.root/name).read_bytes())
        return self.containers[name]
    def sprite(self,name,idx):
        k=(name,idx)
        if k not in self.sprites: self.sprites[k]=parse_sprite(self.chunks(name)[idx])
        return self.sprites[k]
    def module(self,spr,i):
        k=(id(spr),i)
        if k not in self.modules: self.modules[k]=module(spr,i)
        return self.modules[k]
    def frame(self,spr,fr):
        k=(id(spr),fr)
        if k not in self.frames: self.frames[k]=frame(spr,fr)
        return self.frames[k]

def load_world(root, world, level):
    b=(Path(root)/f'w{world}.bin').read_bytes(); pos=2
    for _ in range(level+1):
        w,h=struct.unpack_from('<HH',b,pos); pos+=4
        layers=[list(b[pos+k*w*h:pos+(k+1)*w*h]) for k in range(3)]
        pos += 3*w*h
    return w,h,layers

def render(root, world, level, out):
    A=Assets(root); W,H,L=load_world(root,world,level); wf=f'{world}.f'
    terrain=A.sprite(wf,2); floor=A.module(A.sprite(wf,3),0)
    img=Image.new('RGBA',(W*TILE,H*TILE),(0,0,0,255))
    def put(spr,fr,x,y):
        fi,(ox,oy)=A.frame(spr,fr)
        if fi: img.alpha_composite(fi,(x*TILE+ox,y*TILE+oy))
    # 1: floor + static terrain
    for y in range(H):
        for x in range(W):
            v=L[0][x+y*W]
            if v < 80 or v > 127: img.alpha_composite(floor,(x*TILE,y*TILE))
            if 80 <= v < 80+len(terrain.frame_count): put(terrain,v-80,x,y)
    # 2: layer-0 objects
    bush=A.sprite(wf,1); boulder=A.sprite(wf,0); diamond=A.sprite('cm.f',2); chest=A.sprite('gen2.f',2)
    known0={23:(A.sprite('gen0.f',9),0)}
    for y in range(H):
        for x in range(W):
            v=L[0][x+y*W]
            if v==0: put(boulder,0,x,y)
            elif v==1: put(diamond,(x+y)%len(diamond.frame_count),x,y)
            elif v==2: put(chest,0,x,y)
            elif v==10: put(bush,0,x,y)
            elif v in known0:
                s,fr=known0[v]; put(s,fr,x,y)
    # 3: layer-2 overlays
    cps=A.sprite('cm.f',6)
    gen0=A.sprite('gen0.f',4); gen3=A.sprite('gen3.f',3)
    for y in range(H):
        for x in range(W):
            v=L[2][x+y*W]
            if v==4: put(cps,0,x,y)
            elif v in (20,21,22,23): put(gen0,(v-20)*2,x,y)
            elif v==33: put(gen3,0,x,y)
            elif v in (117,118,119): put(terrain,v-80,x,y)
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    img.convert('RGB').save(out)
    return W,H

def main():
    ap=argparse.ArgumentParser(description='Render one Diamond Rush map with the confirmed layer priority.')
    ap.add_argument('root'); ap.add_argument('world',type=int,help='1..3'); ap.add_argument('level',type=int,help='1-based level number'); ap.add_argument('output')
    a=ap.parse_args()
    if not 1<=a.world<=3: ap.error('world must be 1..3')
    W,H=render(a.root,a.world-1,a.level-1,a.output)
    print(f'rendered world {a.world} level {a.level}: {W}x{H} tiles -> {a.output}')
if __name__=='__main__': main()
