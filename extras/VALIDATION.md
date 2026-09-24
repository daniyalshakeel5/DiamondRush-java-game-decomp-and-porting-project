# Validation checklist

## World parser

For each world file:

- header version must be `1`
- level count must match the file
- every level has exactly three `width*height` layer payloads
- no trailing bytes remain after the last level

The decoder/encoder pair uses `^ 0x55` and is intended to round-trip the stored world binaries byte-for-byte.

## Renderer

The renderer uses the raw stored world files and the extracted `.f` assets. It currently performs these passes:

1. floor
2. layer-0 terrain
3. layer-0 objects
4. layer-2 overlays/objects

Level 1's 26×21 geometry produces a 624×504 PNG.

Unknown IDs are not automatically converted to arbitrary terrain. They remain absent from the object passes until a mapping is established.
