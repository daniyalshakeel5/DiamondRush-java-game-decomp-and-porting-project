"""
Diamond Rush (Gameloft J2ME v1.0.9, 176x208 build) -- Python engine, v0.1

Ships NO game data. Point it at your own copy of the .jar; all graphics and
levels are read from it at runtime.

The engine is display-independent: Game.update() advances one tick (30 Hz) and
Game.render() returns a 176x208 Pillow image, so it can be tested headless and
shown with pygame (play.py) or anything else.
"""
import struct
import zipfile
from PIL import Image, ImageDraw

from gl_sprite import read_container, parse_sprite

TILE = 24
VW, VH = 176, 208            # original phone screen
SPEED = 4                    # pixels per tick (same as the original)
STEPS = TILE // SPEED
TURN_TICKS = 6               # hold time after turning before walking starts (tap = turn only)
DIRS = {'left': (-1, 0), 'up': (0, -1), 'right': (1, 0), 'down': (0, 1)}

# object ids in layer 0 (values < 80); terrain tiles are 80..127
OBJ_BOULDER, OBJ_DIAMOND, OBJ_CHEST, OBJ_BUSH = 0, 1, 2, 10
OBJ_EXIT, OBJ_SNAKE, OBJ_START = 12, 19, 79
LAYER_CHECKPOINT = 4         # value in layer 2

# -- tools (see GAME_LOGIC_NOTES.md section 7c/7i) ---------------------------
# type 4 pickup grants the hammer that breaks type-9 walls; type 5 grants the
# one that breaks type-8 walls. Confirmed in the decompiled pickup code.
TOOL_PICKUPS = {4: 'hammer_a', 5: 'hammer_b'}
WALL_TOOL = {9: 'hammer_a', 8: 'hammer_b'}
# Tibet-exclusive types (never appear in Angkor/Scotland) -- best guess is an
# ice-specific breakable wall pair, requiring a third tool. UNCONFIRMED: we
# have not found the ice mallet's pickup type id yet, nor proven 44/45 behave
# like 8/9 rather than something else. Treat this block as a hypothesis to
# test in the dev room, not an established fact like the two lines above.
ICE_WALL_TOOL = {44: 'ice_mallet', 45: 'ice_mallet'}
HOOKSHOT_RANGE = 2           # tiles; pulls boulders/gems (PLAYER-REPORTED)


def blit(dst, src, x, y):
    """alpha-composite src onto dst at (x, y) with clipping."""
    if x >= dst.width or y >= dst.height or x + src.width <= 0 or y + src.height <= 0:
        return
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(src.width, dst.width - x), min(src.height, dst.height - y)
    dst.alpha_composite(src.crop((sx, sy, ex, ey)), (x + sx, y + sy))


def s8(v):
    return v - 256 if v > 127 else v


class Assets:
    """Reads everything from the user's own jar."""

    def __init__(self, jar_path):
        self.z = zipfile.ZipFile(jar_path)
        names = set(self.z.namelist())
        if 'w0.bin' not in names or 'o.f' not in names:
            raise ValueError('This does not look like the Gameloft Diamond Rush jar '
                             '(expected w0.bin and o.f inside).')
        self._chunks, self._sprites, self._mods, self._frames = {}, {}, {}, {}
        self.worlds = [self._load_world(i) for i in range(3)]

    # -- containers / sprites ------------------------------------------------
    def chunks(self, name):
        if name not in self._chunks:
            self._chunks[name] = read_container(self.z.read(name))
        return self._chunks[name]

    def sprite(self, name, idx):
        key = (name, idx)
        if key not in self._sprites:
            self._sprites[key] = parse_sprite(self.chunks(name)[idx])
        return self._sprites[key]

    def module(self, spr, m, pal=0):
        key = (id(spr), m, pal)
        if key not in self._mods:
            w, h = spr.sizes[m]
            px = spr.module_pixels(m, pal)
            im = Image.new('RGBA', (w, h))
            im.putdata([((c >> 16) & 255, (c >> 8) & 255, c & 255, (c >> 24) & 255) for c in px])
            self._mods[key] = im
        return self._mods[key]

    def frame(self, spr, fr, pal=0):
        """composed frame -> (image, (x0, y0)); origin offsets relative to draw position."""
        key = (id(spr), fr, pal)
        if key in self._frames:
            return self._frames[key]
        st, cnt = spr.frame_start[fr], spr.frame_count[fr]
        parts = []
        for k in range(cnt):
            e = spr.fm[(st + k) * 4:(st + k) * 4 + 4]
            mod, mx, my, mf = e[0], s8(e[1]), s8(e[2]), e[3]
            if len(spr.sizes) > 256:
                mod |= (mf & 0xC0) << 2
            if mod >= len(spr.sizes):
                continue
            w, h = spr.sizes[mod]
            if w > 0 and h > 0:
                parts.append((mod, mx, my, mf, w, h))
        if not parts:
            self._frames[key] = (None, (0, 0))
            return self._frames[key]
        x0 = min(p[1] for p in parts); y0 = min(p[2] for p in parts)
        x1 = max(p[1] + p[4] for p in parts); y1 = max(p[2] + p[5] for p in parts)
        im = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0))
        for mod, mx, my, mf, w, h in parts:
            t = self.module(spr, mod, pal)
            if mf & 1: t = t.transpose(Image.FLIP_LEFT_RIGHT)
            if mf & 2: t = t.transpose(Image.FLIP_TOP_BOTTOM)
            im.alpha_composite(t, (mx - x0, my - y0))
        self._frames[key] = (im, (x0, y0))
        return self._frames[key]

    def frame_flipped(self, spr, fr, pal=0):
        key = (id(spr), fr, pal, 'flip')
        if key not in self._frames:
            im, (x0, y0) = self.frame(spr, fr, pal)
            if im is None:
                self._frames[key] = (None, (0, 0))
            else:   # mirror about the tile centre
                self._frames[key] = (im.transpose(Image.FLIP_LEFT_RIGHT), (TILE - (x0 + im.width), y0))
        return self._frames[key]

    # -- levels --------------------------------------------------------------
    def _load_world(self, i):
        d = self.z.read(f'w{i}.bin')
        (n,) = struct.unpack('<I', d[:4])
        p = d[4:4 + n]
        pos, levels = 2, []
        for _ in range(p[1]):
            w, h = struct.unpack('<HH', p[pos:pos + 4]); pos += 4
            L = [list(p[pos + k * w * h:pos + (k + 1) * w * h]) for k in range(3)]
            pos += 3 * w * h
            levels.append(dict(w=w, h=h, layers=L))
        return levels


class Boulder:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.mv = None           # (dx, dy) while moving
        self.prog = 0
        self.travel = 0          # horizontal pixels rolled (for spin animation)


class Game:
    def __init__(self, assets, world=0, level=0):
        self.A = assets
        self.world, self.level = world, level
        self.debug = True
        self.load(world, level)

    # -- setup ---------------------------------------------------------------
    def load(self, world, level, synthetic_lv=None):
        """synthetic_lv lets a dev/test room bypass the jar's level list entirely
        while reusing all the normal object-parsing and physics setup below."""
        A = self.A
        self.world, self.level = world, level
        lv = synthetic_lv if synthetic_lv is not None else A.worlds[world][level]
        self.W, self.H = lv['w'], lv['h']
        L0, L2 = lv['layers'][0], lv['layers'][2]
        self.raw = L0
        self.tick = 0
        self.state = 'play'
        self.bushes, self.diamonds, self.chests = set(), set(), set()
        self.unknown, self.checkpoints, self.exits = {}, set(), set()
        self.boulders, self.cell_boulder, self.pickups = [], {}, {}
        start = None
        for y in range(self.H):
            for x in range(self.W):
                v = L0[x + y * self.W]
                if L2[x + y * self.W] == LAYER_CHECKPOINT:
                    self.checkpoints.add((x, y))
                if v >= 80:
                    continue
                if v == OBJ_BOULDER:
                    b = Boulder(x, y); self.boulders.append(b); self.cell_boulder[(x, y)] = b
                elif v == OBJ_DIAMOND: self.diamonds.add((x, y))
                elif v == OBJ_CHEST: self.chests.add((x, y))
                elif v == OBJ_BUSH: self.bushes.add((x, y))
                elif v == OBJ_EXIT: self.exits.add((x, y))
                elif v == OBJ_START: start = (x, y)
                elif v in TOOL_PICKUPS: self.pickups[(x, y)] = TOOL_PICKUPS[v]
                else: self.unknown[(x, y)] = v
        self.total_diamonds = len(self.diamonds)
        self.collected = 0
        if start is None:
            start = next(((x, y) for y in range(self.H) for x in range(self.W) if not self.solid(x, y)), (0, 0))
        self.px, self.py = start
        self.respawn = start
        self.active_cp = {start}
        self.face = 'down'
        self.pmove = None        # (dx, dy, prog)
        self.pushing = False
        self.walk_px = 0
        self.prev_held = None
        self.turn_wait = 0
        if synthetic_lv is None:
            # tools are per-level inventory in the original (see 7c); a fresh level
            # starts with none owned unless this Game object already had some
            # (e.g. carried over by the caller for testing).
            self.tools = getattr(self, 'tools', set())
        # else: dev room decides self.tools itself, see load_devroom()
        self.use_flash = None    # ((x,y), ticks_left) - last tool-use target, for the debug overlay
        self._build_static()

    def _build_static(self):
        A, W, H = self.A, self.W, self.H
        tiles = A.sprite(f'{self.world}.f', 2)
        floor = A.module(A.sprite(f'{self.world}.f', 3), 0)
        img = Image.new('RGBA', (W * TILE, H * TILE), (0, 0, 0, 255))
        for y in range(H):
            for x in range(W):
                v = self.raw[x + y * W]
                if v < 80 or v > 127:
                    img.alpha_composite(floor, (x * TILE, y * TILE))
                if 80 <= v < 80 + len(tiles.frame_count):
                    fi, (ox, oy) = A.frame(tiles, v - 80)
                    if fi is not None:
                        blit(img, fi, x * TILE + ox, y * TILE + oy)
        self.static = img

    # -- queries -------------------------------------------------------------
    def inb(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H

    def solid(self, x, y):
        return not self.inb(x, y) or 80 <= self.raw[x + y * self.W] <= 127

    def player_cells(self):
        cells = {(self.px, self.py)}
        if self.pmove:
            cells.add((self.px + self.pmove[0], self.py + self.pmove[1]))
        return cells

    def free_for_boulder(self, x, y):
        return (not self.solid(x, y) and (x, y) not in self.bushes and (x, y) not in self.diamonds
                and (x, y) not in self.chests and (x, y) not in self.cell_boulder
                and (x, y) not in self.player_cells())

    def can_enter(self, x, y):
        return not self.solid(x, y) and (x, y) not in self.chests

    # -- boulders ------------------------------------------------------------
    def _start_boulder(self, b, d):
        b.mv, b.prog = d, 0
        self.cell_boulder[(b.x + d[0], b.y + d[1])] = b

    def _advance_boulders(self):
        for b in self.boulders:
            if b.mv:
                b.prog += SPEED
                if b.mv[0]:
                    b.travel += SPEED
                if b.prog >= TILE:
                    del self.cell_boulder[(b.x, b.y)]
                    b.x, b.y = b.x + b.mv[0], b.y + b.mv[1]
                    b.mv, b.prog = None, 0

    def _gravity(self):
        idle = [b for b in self.boulders if not b.mv]
        # 1) falling: bottom-to-top so a whole column drops together
        for b in sorted(idle, key=lambda b: -b.y):
            if self.free_for_boulder(b.x, b.y + 1):
                self._start_boulder(b, (0, 1))
        # 2) rolling: top-to-bottom -- the topmost boulder of a stack always has priority
        for b in sorted(idle, key=lambda b: b.y):
            if b.mv:
                continue
            support = self.cell_boulder.get((b.x, b.y + 1))
            if support is None or support.mv:
                continue                                   # not resting on a settled boulder
            if (b.x, b.y - 1) in self.cell_boulder:
                continue                                   # something is stacked on it: top one goes first
            for dx in (-1, 1):                             # roll toward an open (unsupported) side
                if self.free_for_boulder(b.x + dx, b.y) and self.free_for_boulder(b.x + dx, b.y + 1):
                    self._start_boulder(b, (dx, 0))
                    break

    # -- player --------------------------------------------------------------
    def _arrive(self):
        c = (self.px, self.py)
        if c in self.bushes:
            self.bushes.discard(c)
        if c in self.diamonds:
            self.diamonds.discard(c); self.collected += 1
        if c in self.checkpoints:
            self.respawn = c; self.active_cp.add(c)
        if c in self.exits:
            self.state = 'won'
        if c in self.pickups:
            self.tools.add(self.pickups.pop(c))

    def try_move(self, name):
        self.face = name
        dx, dy = DIRS[name]
        tx, ty = self.px + dx, self.py + dy
        if not self.can_enter(tx, ty):
            return False
        b = self.cell_boulder.get((tx, ty))
        self.pushing = False
        if b:
            if b.mv or not self.free_for_boulder(tx + dx, ty + dy):
                return False
            self._start_boulder(b, (dx, dy))
            self.pushing = True
        self.pmove = (dx, dy, 0)
        return True

    def _advance_player(self, held):
        new_press = held != self.prev_held
        self.prev_held = held
        if self.pmove:
            dx, dy, prog = self.pmove
            prog += SPEED
            self.walk_px += SPEED
            if prog >= TILE:
                self.px, self.py = self.px + dx, self.py + dy
                self.pmove = None
                self.pushing = False
                self._arrive()
                if self.state != 'play':
                    return
            else:
                self.pmove = (dx, dy, prog)
                return
        if not held:
            self.turn_wait = 0
            return
        if held != self.face:                 # first tap only turns the player
            self.face = held
            self.turn_wait = TURN_TICKS
            return
        if self.turn_wait > 0 and not new_press:   # key kept down after turning: short delay, then walk
            self.turn_wait -= 1
            return
        self.turn_wait = 0
        self.try_move(held)

    # -- tools -----------------------------------------------------------
    def use(self):
        """Use whatever tool applies in front of the player: hammer/ice mallet
        against a matching breakable wall, else hookshot to pull the nearest
        boulder/gem within HOOKSHOT_RANGE tiles. Returns a short string saying
        what happened, for debug/testing -- not part of normal render output."""
        dx, dy = DIRS[self.face]
        tx, ty = self.px + dx, self.py + dy
        v = self.raw[tx + ty * self.W] if self.inb(tx, ty) else None
        for wall_map, label in ((WALL_TOOL, 'wall'), (ICE_WALL_TOOL, 'ice wall')):
            if v in wall_map:
                if wall_map[v] not in self.tools:
                    return f'need {wall_map[v]} to break this {label}'
                self.raw[tx + ty * self.W] = 255           # becomes open floor
                self._build_static()                        # terrain image must be redrawn
                self.use_flash = ((tx, ty), 6)
                return f'broke {label} at {(tx, ty)} with {wall_map[v]}'
        # hookshot: first pullable object in a straight line, up to HOOKSHOT_RANGE tiles
        if 'hookshot' not in self.tools:
            return 'no hookshot owned'
        for dist in range(1, HOOKSHOT_RANGE + 1):
            cx, cy = self.px + dx * dist, self.py + dy * dist
            if not self.inb(cx, cy) or self.solid(cx, cy):
                break
            b = self.cell_boulder.get((cx, cy))
            if b or (cx, cy) in self.diamonds:
                dest = (self.px + dx, self.py + dy)
                if not self.free_for_boulder(*dest) and dest not in self.diamonds:
                    return 'hookshot: nowhere to pull it to'
                if b:
                    del self.cell_boulder[(b.x, b.y)]
                    b.x, b.y = dest
                    self.cell_boulder[dest] = b
                else:
                    self.diamonds.discard((cx, cy)); self.diamonds.add(dest)
                self.use_flash = (dest, 6)
                return f'hookshot pulled object from {(cx, cy)} to {dest}'
        return 'hookshot: nothing in range'

    def update(self, held=None, action=False):
        """advance one 30 Hz tick; held is 'left'/'up'/'right'/'down' or None;
        action=True triggers a tool use this tick (rising edge is the caller's job)."""
        self.tick += 1
        if self.use_flash and self.use_flash[1] > 0:
            self.use_flash = (self.use_flash[0], self.use_flash[1] - 1)
        if self.state != 'play':
            return
        if action:
            self.use()
        self._advance_boulders()
        self._gravity()              # must run before the player can push again
        self._advance_player(held)

    # -- rendering -----------------------------------------------------------
    def _player_frame(self):
        A = self.A
        spr = A.sprite('o.f', 0)
        f = self.face
        flip = (f == 'left')
        if self.pmove and self.pushing:
            anim = 5 if f in ('left', 'right') else 8
        elif self.pmove:
            anim = {'up': 4, 'down': 6}.get(f, 1)
        else:
            frame = {'up': 72, 'down': 73}.get(f, 62)
            return frame, flip
        st, cnt = spr.anim_start[anim], spr.anim_count[anim]
        idx = (self.walk_px // 3) % cnt
        return spr.anim_frames[(st + idx) * 5], flip

    def render(self):
        A = self.A
        pxp = self.px * TILE + (self.pmove[0] * self.pmove[2] if self.pmove else 0)
        pyp = self.py * TILE + (self.pmove[1] * self.pmove[2] if self.pmove else 0)
        cw, ch = self.W * TILE, self.H * TILE
        camx = pxp + TILE // 2 - VW // 2
        camy = pyp + TILE // 2 - VH // 2
        camx = (cw - VW) // 2 if cw <= VW else max(0, min(cw - VW, camx))
        camy = (ch - VH) // 2 if ch <= VH else max(0, min(ch - VH, camy))
        out = Image.new('RGBA', (VW, VH), (0, 0, 0, 255))
        out.paste(self.static, (-camx, -camy))

        def put(im, x, y):
            if im is not None:
                blit(out, im, x - camx, y - camy)

        bush = A.sprite(f'{self.world}.f', 1)
        for (x, y) in self.bushes:
            im, (ox, oy) = A.frame(bush, 0)
            put(im, x * TILE + ox, y * TILE + oy)
        dspr = A.sprite('cm.f', 2)
        for (x, y) in self.diamonds:
            im, (ox, oy) = A.frame(dspr, (self.tick // 6 + x + y) % len(dspr.frame_count))
            put(im, x * TILE + ox, y * TILE + oy)
        cps = A.sprite('cm.f', 6)
        for (x, y) in self.checkpoints:
            im, (ox, oy) = A.frame(cps, 0)
            put(im, x * TILE + ox, y * TILE + oy)
        chest = A.sprite('gen2.f', 2)
        for (x, y) in self.chests:
            im, (ox, oy) = A.frame(chest, 0)
            put(im, x * TILE + ox, y * TILE + oy)
        bspr = A.sprite(f'{self.world}.f', 0)
        for b in self.boulders:
            bx, by = b.x * TILE, b.y * TILE
            if b.mv:
                bx += b.mv[0] * b.prog; by += b.mv[1] * b.prog
            im, (ox, oy) = A.frame(bspr, (b.travel // 3) % 8)
            put(im, bx + ox, by + oy)
        if self.debug:
            d = ImageDraw.Draw(out)
            for (x, y), v in self.unknown.items():
                sx, sy = x * TILE - camx, y * TILE - camy
                d.rectangle([sx + 3, sy + 3, sx + TILE - 4, sy + TILE - 4], outline=(255, 60, 60, 255))
                d.text((sx + 5, sy + 7), str(v), fill=(255, 255, 0, 255))
            # dev room: label every placed id, including ones that already render a real sprite
            for (x, y), v in getattr(self, 'devroom_ids', {}).items():
                sx, sy = x * TILE - camx, y * TILE - camy
                d.rectangle([sx, sy - 10, sx + 22, sy - 1], fill=(0, 0, 0, 200))
                d.text((sx + 2, sy - 10), str(v), fill=(120, 255, 120, 255))
            if self.use_flash and self.use_flash[1] > 0:
                (ux, uy), _ = self.use_flash
                sx, sy = ux * TILE - camx, uy * TILE - camy
                d.rectangle([sx + 1, sy + 1, sx + TILE - 2, sy + TILE - 2], outline=(80, 255, 80, 255), width=2)
        pspr = A.sprite('o.f', 0)
        fr, flip = self._player_frame()
        im, (ox, oy) = (A.frame_flipped if flip else A.frame)(pspr, fr)
        put(im, pxp + ox, pyp + oy)
        d = ImageDraw.Draw(out)
        tool_str = ' '.join(sorted(self.tools)) if self.tools else 'none'
        hud = f'GEMS {self.collected}/{self.total_diamonds}  W{self.world + 1}-{self.level + 1}  TOOLS:{tool_str}'
        d.rectangle([0, 0, min(VW, 6 * len(hud) + 6), 11], fill=(0, 0, 0, 170))
        d.text((3, 0), hud, fill=(255, 255, 255, 255))
        if self.state == 'won':
            d.rectangle([0, VH // 2 - 14, VW, VH // 2 + 14], fill=(0, 0, 0, 200))
            d.text((VW // 2 - 40, VH // 2 - 6), 'LEVEL COMPLETE', fill=(255, 230, 80, 255))
        return out.convert('RGB')

    # -- convenience ---------------------------------------------------------
    def restart(self):
        self.load(self.world, self.level)

    def goto(self, world, level):
        world %= len(self.A.worlds)
        level %= len(self.A.worlds[world])
        self.load(world, level)

    # -- dev room --------------------------------------------------------
    def load_devroom(self, world=None):
        """One of every object type id ever seen in any level's layer 0, laid
        out on an open floor in a labelled grid, so every id can be walked up
        to, hit with a tool, and matched against real footage. Known types
        (boulder/diamond/chest/bush) render with their real sprite as usual;
        everything else shows as a numbered red box until it gets identified
        and given its own branch in load()'s parsing loop. All tools are
        granted so hammer/ice-mallet/hookshot can be tested on every id."""
        if world is not None:
            self.world = world
        ids = sorted({v for lv in self.A.worlds[self.world] for v in lv['layers'][0] if v < 80})
        cols, spacing, margin = 10, 3, 2
        rows = (len(ids) + cols - 1) // cols
        w = margin * 2 + cols * spacing
        h = margin * 2 + 3 + rows * spacing
        L0 = [255] * (w * h)
        L0[(margin) + (margin) * w] = OBJ_START            # player starts top-left, above the grid
        for i, v in enumerate(ids):
            gx = margin + (i % cols) * spacing
            gy = margin + 3 + (i // cols) * spacing
            L0[gx + gy * w] = v
        lv = dict(w=w, h=h, layers=[L0, [0] * (w * h), [0] * (w * h)])
        self.tools = {'hammer_a', 'hammer_b', 'ice_mallet', 'hookshot'}
        self.load(self.world, 0, synthetic_lv=lv)
        self.debug = True
        self.devroom_ids = {(margin + (i % cols) * spacing, margin + 3 + (i // cols) * spacing): v
                             for i, v in enumerate(ids)}
        return ids
