# Diamond Rush J2ME Reverse-Engineering Notes

## Project

These notes record the binary-format and asset findings from reconstructing the Nokia N70 J2ME version of **Diamond Rush**.

Target:

- `Diamond-Rush_J2ME_EN_v109-Nokia-N70.jar`
- J2ME / Nokia N70 build
- Native game screen: 240×320
- Native map tile size: **24×24 pixels**
- World files: `w0.bin`, `w1.bin`, `w2.bin`

Project repository:

https://github.com/daniyalshakeel5/DiamondRush-java-game-decomp-and-porting-project

Useful external references:

- https://github.com/kubikaugustyn/DiamondRushSource
- https://github.com/palaceswitcher/Diamond-Rush-Decomp
- https://github-wiki-see.page/m/palaceswitcher/Gameloft-J2ME-Tools/wiki/Asset-Pack-Format

---

# 1. World-file format

`w0.bin`, `w1.bin`, and `w2.bin` are sequential level containers.

## Header

The first two bytes are:

```text
byte 0: format/version = 0x01
byte 1: number of levels
```

Observed values:

| File | Version | Levels | File size |
|---|---:|---:|---:|
| `w0.bin` | `1` | 14 | 47,686 |
| `w1.bin` | `1` | 13 | 46,956 |
| `w2.bin` | `1` | 14 | 56,887 |

After the two-byte world header, each level begins with:

```text
uint16 width   (little-endian)
uint16 height  (little-endian)
```

Then:

```text
width * height bytes  layer 0
width * height bytes  layer 1
width * height bytes  layer 2
```

The next level header follows immediately. There is no level-offset index at the start.

## Decoding

The three layer payloads are XOR-obfuscated with:

```text
0x55
```

So:

```text
decoded = stored ^ 0x55
stored  = decoded ^ 0x55
```

The world header and width/height fields are not XORed.

Example:

```text
01 0E 1A 00 15 00
```

means:

```text
version     = 1
level count = 14
width       = 26
height      = 21
```

The first stored payload bytes include:

```text
61 6B 55 55 55 ...
```

which decode to:

```text
34 3E 00 00 00 ...
```

## Empty cell

Stored `0xFF` becomes:

```text
0xFF ^ 0x55 = 0xAA
```

Thus `0xAA` is the observed decoded empty/unused cell value.

Do not confuse it with decoded `0x00`; `0x00` occurs as real map data.

---

# 2. Complete level dimensions

## World 1 — `w0.bin`

| Level | Width | Height | Pixels |
|---:|---:|---:|---:|
| 1 | 26 | 21 | 624×504 |
| 2 | 27 | 24 | 648×576 |
| 3 | 27 | 26 | 648×624 |
| 4 | 40 | 23 | 960×552 |
| 5 | 51 | 24 | 1224×576 |
| 6 | 30 | 75 | 720×1800 |
| 7 | 26 | 45 | 624×1080 |
| 8 | 44 | 29 | 1056×696 |
| 9 | 35 | 14 | 840×336 |
| 10 | 50 | 30 | 1200×720 |
| 11 | 50 | 31 | 1200×744 |
| 12 | 46 | 31 | 1104×744 |
| 13 | 46 | 31 | 1104×744 |
| 14 | 68 | 11 | 1632×264 |

## World 2 — `w1.bin`

| Level | Width | Height | Pixels |
|---:|---:|---:|---:|
| 1 | 45 | 24 | 1080×576 |
| 2 | 40 | 24 | 960×576 |
| 3 | 33 | 30 | 792×720 |
| 4 | 43 | 30 | 1032×720 |
| 5 | 45 | 33 | 1080×792 |
| 6 | 43 | 33 | 1032×792 |
| 7 | 36 | 43 | 864×1032 |
| 8 | 53 | 27 | 1272×648 |
| 9 | 34 | 32 | 816×768 |
| 10 | 35 | 25 | 840×600 |
| 11 | 37 | 24 | 888×576 |
| 12 | 60 | 20 | 1440×480 |
| 13 | 23 | 60 | 552×1440 |

## World 3 — `w2.bin`

| Level | Width | Height | Pixels |
|---:|---:|---:|---:|
| 1 | 60 | 26 | 1440×624 |
| 2 | 39 | 35 | 936×840 |
| 3 | 35 | 42 | 840×1008 |
| 4 | 38 | 38 | 912×912 |
| 5 | 46 | 27 | 1104×648 |
| 6 | 49 | 28 | 1176×672 |
| 7 | 55 | 30 | 1320×720 |
| 8 | 51 | 20 | 1224×480 |
| 9 | 51 | 37 | 1224×888 |
| 10 | 104 | 17 | 2496×408 |
| 11 | 35 | 25 | 840×600 |
| 12 | 45 | 28 | 1080×672 |
| 13 | 35 | 32 | 840×768 |
| 14 | 35 | 26 | 840×624 |

Total: **41 levels**.

---

# 3. Layer representation and indexing

Every level contains exactly three `W*H` arrays. The tools call them:

```text
layer 0
layer 1
layer 2
```

These names are deliberately neutral because the original renderer is still partly obfuscated.

The flat array is addressed as:

```text
index = y * width + x
```

so `x` changes fastest.

Layer 0 has the densest set of IDs. Layers 1 and 2 are generally much sparser and contain additional terrain/object/decoration information.

The parser preserves all three layers without trying to interpret IDs.

---

# 4. `.f` resource containers

The `.f` files use the Gameloft offset+size resource-container format.

For the files in this game:

```text
byte 0:
    resource count

for each resource:
    uint32 little-endian relative offset
    uint32 little-endian size

payload:
    resources at header_size + relative_offset
```

where:

```text
header_size = 1 + 8 * resource_count
```

Example: `0.f` begins with `04`, so it contains four resources.

Observed `0.f` table:

| Resource | Relative offset | Size |
|---:|---:|---:|
| 0 | `0x0000` | `0x09B6` |
| 1 | `0x09B6` | `0x04EE` |
| 2 | `0x0EA4` | `0x2323` |
| 3 | `0x31C7` | `0x0150` |

The last resource ends exactly at the end of the payload.

The internal resources commonly begin with:

```text
DF 03 01 01 01 01 ...
```

The container format is documented here:

https://github-wiki-see.page/m/palaceswitcher/Gameloft-J2ME-Tools/wiki/Asset-Pack-Format

---

# 5. Sprite/resource counts

Observed resource counts in the main terrain packs:

| File | Resource frame counts | Total |
|---|---|---:|
| `0.f` | 8 + 13 + 30 + 1 | 52 |
| `1.f` | 5 + 20 + 39 + 1 | 65 |
| `2.f` | 8 + 9 + 33 + 1 | 51 |

These totals match the sprite atlases extracted during the reconstruction.

A world byte is **not** simply "frame N of `N.f`". Multiple resource packs and another lookup stage are involved.

---

# 6. `mc`

The file `mc` is exactly 256 bytes and behaves as a lookup table.

It contains mappings in several ranges and is involved in the map-ID/resource lookup path.

It should **not** be treated as a standalone direct:

```text
map ID -> PNG frame
```

table.

The complete semantic mapping of every entry is not yet frozen.

---

# 7. Important ID observations

Decoded maps contain IDs far beyond the 0–51 range. Examples include values around 79–125 and, in later worlds, IDs above 200.

A particularly important value is:

```text
170 decimal = 0xAA
```

which is the decoded form of stored `0xFF` and is therefore the observed empty cell.

This is why a naive "every decoded byte is a sprite index" renderer produces incorrect results.

---

# 8. Validation reference

The supplied reference level image is:

```text
624 × 504 pixels
```

which exactly equals:

```text
26 × 21 tiles × 24 × 24 pixels
```

That matches World 1 / Level 1 from `w0.bin` and was used as the primary geometry/rendering validation target.

Full-size PNGs were generated for all 41 levels during the reconstruction, along with debug maps containing unresolved IDs.

---

# 9. What is solved

Confirmed:

- sequential world container structure
- version byte
- level count
- little-endian width/height
- exactly three layers per level
- `0x55` payload XOR
- empty-cell transformation `FF -> AA`
- all 41 level dimensions
- 24×24 native map tile size
- `.f` offset+size container structure
- `.f` resource offsets/sizes
- major resource/frame counts
- raw decoded representation of every level
- lossless world-file round-trip

The included encoder was tested by decoding the supplied world files and then rebuilding them. The rebuilt `w0.bin`, `w1.bin`, and `w2.bin` were **byte-for-byte identical** to the originals.

---

# 10. What remains

Not yet completely frozen:

- exact map-ID -> resource/frame mapping for every ID
- complete internal `DF 03 ...` sprite decoder
- exact three-layer draw order in every situation
- multi-tile object composition
- animated object handling
- enemy/mechanism/trigger semantics

The binary level format itself is therefore no longer the main blocker; the remaining work is the renderer/resource mapping layer.

---

# 11. Included tools

### `decode_worlds.py`

Decodes `w0.bin`, `w1.bin`, `w2.bin` to JSON/CSV and optional ID-debug PNGs.

### `encode_worlds.py`

Inverse operation. Rebuilds the original world files from decoded JSON, using the `^ 0x55` transform.

### `inspect_f_pack.py`

Prints `.f` resource counts, offsets, sizes, boundaries, and resource previews.

### `levels.json`

The decoded 41-level dataset produced during this investigation.

---

# 12. Suggested continuation

For the next phase of the port:

1. Locate the Java code that opens `w0`, `w1`, and `w2`.
2. Locate every use of `mc`.
3. Trace the loaded `.f` resource arrays.
4. Identify the final map-ID -> resource/frame lookup.
5. Identify exact layer draw order.
6. Identify special multi-tile objects and animations.
7. Replace the provisional renderer with the exact Java-equivalent renderer.
8. Pixel-validate World 1 / Level 1 against the supplied reference.


---

# 8. Renderer notes

The binary-format decoder and the graphical renderer are separate stages. The decoder above preserves the `^ 0x55` representation for analysis and byte-for-byte reconstruction. The current renderer reads the raw stored world files because that matches the engine-side representation used by the current rendering implementation.

See `RENDERING_PIPELINE.md` for the confirmed graphical pass order:

```text
floor -> layer-0 terrain -> layer-0 objects -> layer-2 overlays
```

The Level 1 reference established this priority pattern; it is now applied consistently to all 41 levels.
