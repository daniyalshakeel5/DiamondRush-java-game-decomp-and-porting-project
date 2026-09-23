"""Gameloft 'BSprite' (.f chunk) parser for Diamond Rush J2ME v1.0.9."""
import struct
from dataclasses import dataclass, field

def u16(b, p): return b[p] | (b[p+1] << 8)

def read_container(data):
    """.f container -> list of chunk bytes."""
    total, n = struct.unpack('<II', data[:8])
    pos = 9
    (l0,) = struct.unpack('<I', data[pos:pos+4]); pos += 4
    ents = [(0, l0)]
    for _ in range(n - 1):
        o, l = struct.unpack('<II', data[pos:pos+8]); pos += 8
        ents.append((o, l))
    return [data[pos+o:pos+o+l] for o, l in ents]

ENC_RLE_A, ENC_4BPP, ENC_2BPP, ENC_1BPP, ENC_8BPP, ENC_RLE_B = 10225, 5632, 1024, 512, 22018, 22258
PAL_ARGB8888, PAL_ARGB4444, PAL_ARGB1555, PAL_RGB565 = 0x8888, 0x4444, 0x5515, 0x6505

@dataclass
class Sprite:
    sizes: list            # [(w,h)] per module
    fm: bytes              # frame-module table, 4 bytes each: (module, x, y, flags)
    frame_count: list      # modules per frame
    frame_start: list      # start index into fm
    anim_frames: bytes     # 5 bytes each: (frame, duration, dx, dy, flags)
    anim_count: list
    anim_start: list
    palettes: list = field(default_factory=list)   # list of list of ARGB ints
    encoding: int = 0
    mod_data: list = field(default_factory=list)

    def module_pixels(self, i, pal=0):
        w, h = self.sizes[i]
        b = self.mod_data[i]; p = 0; n = w * h
        colors = self.palettes[pal]; out = []
        enc = self.encoding
        if enc == ENC_RLE_A:
            while len(out) < n:
                v = b[p]; p += 1
                if v > 127:
                    c = colors[b[p]]; p += 1
                    out += [c] * (v - 128)
                else:
                    out.append(colors[v])
        elif enc == ENC_4BPP:
            while len(out) < n:
                out += [colors[b[p] >> 4 & 15], colors[b[p] & 15]]; p += 1
        elif enc == ENC_2BPP:
            while len(out) < n:
                v = b[p]; p += 1
                out += [colors[v >> s & 3] for s in (6, 4, 2, 0)]
        elif enc == ENC_1BPP:
            while len(out) < n:
                v = b[p]; p += 1
                out += [colors[v >> s & 1] for s in range(7, -1, -1)]
        elif enc == ENC_8BPP:
            out = [colors[x] for x in b[:n]]
        elif enc == ENC_RLE_B:
            while len(out) < n:
                v = b[p]; p += 1
                if v > 127:
                    for _ in range(v - 128):
                        out.append(colors[b[p]]); p += 1
                else:
                    c = colors[b[p]]; p += 1
                    out += [c] * v
        else:
            raise ValueError(f'unknown pixel encoding {enc}')
        return out[:n]

def parse_sprite(b):
    p = 6
    nmod = u16(b, p); p += 2
    sizes = [(b[p+2*i], b[p+2*i+1]) for i in range(nmod)]; p += nmod * 2
    s = u16(b, p); p += 2
    fm = b[p:p+s*4]; p += s * 4
    nfr = u16(b, p); p += 2
    fc, fs = [], []
    for _ in range(nfr):
        fc.append(b[p]); fs.append(u16(b, p+2)); p += 4
    p += nfr * 4                       # per-frame extra 4 bytes (bounds?)
    nan = u16(b, p); p += 2
    af = b[p:p+nan*5]; p += nan * 5
    nanim = u16(b, p); p += 2
    ac, a_s = [], []
    for _ in range(nanim):
        ac.append(b[p]); a_s.append(u16(b, p+2)); p += 4
    spr = Sprite(sizes, fm, fc, fs, af, ac, a_s)
    if nmod <= 0:
        return spr
    fmt = u16(b, p); p += 2
    npal = b[p]; ncol = b[p+1]; p += 2
    for _ in range(npal):
        pal = []
        for _ in range(ncol):
            if fmt == PAL_ARGB8888:
                v = int.from_bytes(b[p:p+4], 'little'); p += 4
            else:
                v16 = u16(b, p); p += 2
                if fmt == PAL_ARGB4444:
                    a=(v16>>12)&15; r=(v16>>8)&15; g=(v16>>4)&15; bl=v16&15
                    v = (a*17<<24)|(r*17<<16)|(g*17<<8)|bl*17
                elif fmt == PAL_ARGB1555:
                    a = 0xFF000000 if v16 & 0x8000 else 0
                    v = a | ((v16&0x7C00)<<9) | ((v16&0x3E0)<<6) | ((v16&0x1F)<<3)
                elif fmt == PAL_RGB565:
                    a = 0 if v16 == 0xF81F else 0xFF000000
                    v = a | ((v16&0xF800)<<8) | ((v16&0x7E0)<<5) | ((v16&0x1F)<<3)
                else:
                    raise ValueError(f'unknown palette fmt {fmt:#x}')
            pal.append(v)
        spr.palettes.append(pal)
    spr.encoding = u16(b, p); p += 2
    for _ in range(nmod):
        n = u16(b, p); p += 2
        spr.mod_data.append(b[p:p+n]); p += n
    return spr
