# Changelog

## 2026-09-25 — layer-priority renderer patch

- Added portable single-level renderer with command-line arguments.
- Removed hard-coded `/mnt/data/workfix/diamond` dependency.
- Applied the confirmed Level 1 rendering order to all 41 levels:
  - floor/background
  - layer-0 terrain
  - layer-0 objects
  - layer-2 overlays/objects
- Kept unknown IDs untouched instead of assigning guessed opaque tiles.
- Added renderer documentation explaining the distinction between binary XOR decoding and the raw map representation consumed by the renderer.
- Added portable decode/encode/`.f` inspection scripts to make the package self-contained.
- Verified all 41 PNGs render successfully.
- Verified decoder -> encoder round-trip produces byte-identical `w0.bin`, `w1.bin`, and `w2.bin`.
