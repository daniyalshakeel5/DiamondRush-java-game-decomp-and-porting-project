# Diamond Rush Renderer Findings

This document records the renderer rules established from the Level 1 reference and applies them as the default priority model for all 41 maps.

## Important distinction: map parsing vs rendering

There are two useful representations of the world files:

1. **Raw world bytes** — the bytes as stored in `w0.bin`, `w1.bin`, and `w2.bin`. The renderer used here consumes these values because that matches the engine-side map representation used by the current renderer implementation.
2. **XOR-decoded analysis data** — `decode_worlds.py` can decode the `^ 0x55` representation used for binary-format analysis and round-trip reconstruction. That decoded JSON is useful for inspecting the map, but it should not be fed directly into the renderer without converting it back to the stored representation.

This distinction prevents the binary-format decoder and the graphical renderer from being conflated.

## Confirmed canvas geometry

Each map cell is 24×24 pixels.

```text
pixel_x = tile_x * 24
pixel_y = tile_y * 24
```

Therefore a map `W × H` becomes `(W*24) × (H*24)`.

World 1 Level 1 is 26×21 tiles = 624×504 pixels, matching the supplied reference.

## Layer priority

The current renderer follows this order:

```text
1. World floor / background
2. Static terrain selected by layer 0 IDs 80..127
3. Layer-0 objects
4. Layer-2 overlays / objects
```

Layer 1 is retained by the parser but is not yet assigned a complete graphical role. It must not be discarded from decoded map data.

The critical point is that priority is **not** equivalent to numerical map-ID order. An object can have a lower numerical ID and still be drawn after terrain because it belongs to a later rendering pass.

## Static terrain

For world `wN.bin`, the matching terrain resources are in `N.f`:

```text
0.f -> world 1
1.f -> world 2
2.f -> world 3
```

The current static renderer uses resource index 2 from that `.f` container as the terrain sprite set and resource index 3 module 0 as the world floor.

Layer-0 terrain values in the 80..127 range select terrain frames using:

```text
frame = layer0_value - 80
```

Only frame indices that actually exist in the resource are drawn.

## Object passes currently implemented

The current renderer carries the known mappings established during the Level 1 investigation:

- layer 0 value `0` -> world boulder/object frame
- layer 0 value `1` -> diamond animation frame
- layer 0 value `2` -> chest
- layer 0 value `10` -> bush
- layer 0 value `23` -> known world-1 object
- layer 2 value `4` -> checkpoint
- layer 2 values `20..23` -> corresponding `gen0.f` object frames
- layer 2 value `33` -> `gen3.f` object
- layer 2 values `117..119` -> world terrain frames 37..39

These are renderer mappings, not claims that the numeric IDs are globally universal across every game build. Unknown IDs are intentionally left untouched until mapped.

## Why this matters

The Level 1 reference demonstrated that the renderer must composite transparent sprites in passes. Rendering each numeric map ID as an opaque tile produces the characteristic incorrect result where the whole map becomes filled with a single background/terrain texture.

The same priority model should therefore be applied consistently to every level while additional object IDs are decoded.

## Current status

### Solved

- world dimensions
- three-layer extraction
- 24×24 tile geometry
- `.f` outer resource container
- sprite/frame decoding used by the renderer
- floor -> terrain -> layer-0 objects -> layer-2 overlays priority
- deterministic generation of all 41 map PNGs

### Still incomplete

- complete ID -> object/frame mapping for every dynamic object
- full interpretation of layer 1
- animation/state-dependent objects
- enemy/player rendering
- any camera/UI composition (the exported PNGs are map canvases, not gameplay screenshots)

Do not treat an unimplemented ID as an empty cell. Unknown IDs are preserved so they can be mapped later.
