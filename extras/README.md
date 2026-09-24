# Diamond Rush J2ME reverse-engineering tools

Tools for extracting, validating, and rendering the 41 maps from the Nokia N70 J2ME version of Diamond Rush.

## Included

- `decode_worlds.py` — decode `w0.bin`/`w1.bin`/`w2.bin` into JSON and CSV analysis data.
- `encode_worlds.py` — rebuild world binaries from decoded JSON.
- `inspect_f_pack.py` — inspect the outer `.f` resource-container tables.
- `render_dr.py` — render a single level using the current confirmed layer-priority pipeline.
- `render_all_levels.py` — render all 41 levels.
- `DIAMOND_RUSH_LEVEL_FORMAT.md` — binary format notes.
- `RENDERING_PIPELINE.md` — graphical renderer and layer-priority notes.
- `levels.json` — decoded level dataset when included.

## Quick start

Install Pillow:

```bash
python -m pip install Pillow
```

Render one level directly from the extracted game directory:

```bash
python render_dr.py /path/to/diamond 0 0 level_01.png
```

Arguments are:

```text
root world_index level_index output.png
```

Both indices are zero-based, so `0 0` means World 1 Level 1.

Render everything:

```bash
python render_all_levels.py /path/to/diamond -o rendered_levels
```

Decode the binary format for analysis:

```bash
python decode_worlds.py /path/to/diamond -o decoded --debug-png
```

Rebuild the original binaries:

```bash
python encode_worlds.py decoded/levels.json -o rebuilt
```

Inspect `.f` files:

```bash
python inspect_f_pack.py /path/to/diamond/0.f /path/to/diamond/1.f /path/to/diamond/2.f
```

## Renderer priority

The current confirmed order is:

```text
floor/background
    ↓
static terrain (layer 0, IDs 80..127)
    ↓
layer-0 objects
    ↓
layer-2 overlays/objects
```

The renderer consumes the **raw stored world representation**. The analysis decoder's XOR-decoded JSON is not the renderer input; use the encoder to return to stored bytes when needed.

## Status

The map format and deterministic static rendering pipeline are established. The remaining reverse-engineering work is mapping every object/dynamic ID and fully determining layer 1. Unknown IDs are preserved rather than silently converted into arbitrary tiles.
