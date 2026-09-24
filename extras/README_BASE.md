# Diamond Rush reverse-engineering tools

## Included

- `DIAMOND_RUSH_LEVEL_FORMAT.md` — complete findings from the level reconstruction.
- `decode_worlds.py` — decode `w0.bin`, `w1.bin`, `w2.bin`.
- `encode_worlds.py` — rebuild world files from decoded JSON.
- `inspect_f_pack.py` — inspect `.f` resource containers.
- `levels.json` — decoded 41-level dataset.
- `VALIDATION.txt` — results of byte-for-byte round-trip testing.

## Decode

```bash
python decode_worlds.py path/to/diamond -o decoded --debug-png
```

`--debug-png` requires:

```bash
pip install pillow
```

The debug PNGs are ID visualizations, not the game's final renderer.

## Re-encode

```bash
python encode_worlds.py decoded/levels.json -o rebuilt
```

The generated `w0.bin`, `w1.bin`, and `w2.bin` can be compared against the originals.

## Inspect .f

```bash
python inspect_f_pack.py path/to/diamond/0.f path/to/diamond/1.f path/to/diamond/2.f
```
