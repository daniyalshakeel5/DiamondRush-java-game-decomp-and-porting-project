# Diamond Rush (Gameloft J2ME) -- Python port, v0.3

A from-scratch Python engine for the 2006 Gameloft phone game. **No game data is
included.** You supply your own copy of the jar (built and tested against
`Diamond-Rush_J2ME_EN_v109-Nokia-N70.jar`, 176x208).

    pip install pygame pillow
    python play.py path/to/Diamond-Rush_J2ME_EN_v109-Nokia-N70.jar

If no path is given it looks for a .jar in the current folder, then opens a file picker.

## Controls
Arrows / WASD: tap a direction to turn, tap again to step one tile, hold to walk -
SPACE use tool (hammer/ice mallet on an adjacent breakable wall, else hookshot on the
nearest boulder/gem within 2 tiles) - F1 dev room (every object id in the current
world, all tools granted; press again to cycle worlds) - F5 back to the real level -
R restart - [ ] previous/next level - 1/2/3 jump to world - TAB toggle debug id boxes
- Enter next level after finishing - Esc quit.

## What works
- Loads all 41 levels from the jar and draws terrain, floor and objects with the
  original graphics.
- Tap-to-turn, then step (hold to walk); the turn/hold delay is `TURN_TICKS` in
  `dr_engine.py`.
- Player walking, bush clearing, diamond pickup, checkpoints, level exit tile.
- Boulders and gems: pushable sideways only (never up/down); fall when unsupported;
  a stacked pair only rolls when actually stacked, with the top one always deciding
  first; a falling boulder lands on the player rather than being blocked by them.
- Player knockback goes in the direction they were already moving, not away from
  the hazard (matches the original).
- Two hammers (picked up from cell types 4 and 5) each break a different wall type
  (9 and 8); a hookshot pulls a boulder or gem up to 2 tiles away in front of the
  player into the adjacent cell. Tool ownership is per-level, like the original.
- **Dev room (F1)**: a synthetic level listing one of every object-type id that
  appears anywhere in the current world's levels, each in its own labelled slot,
  with every tool granted. Known types (boulder/diamond/chest/bush) render with
  their real sprite; everything else is a walkable slot labelled with its numeric
  id, meant for side-by-side comparison against real footage. Confirmed while
  building this: the "bush" slot renders as a cobweb in Scotland and a bubble in
  Tibet -- one object type, reskinned per world, matching the "bushes/cobwebs/
  bubbles behave the same" note.

## Not done yet (red/green boxes with numbers = objects not implemented)
Enemies (snakes, Tibetan warriors, etc.) and their AI, chests' contents, doors and
keys, pressure plates, sluice gates, water/buoyancy, the freeze-beam statue and a
frozen player/enemy state, mine explosions, checkpoint-triggered full room reset
(confirmed in the original's code but not yet wired into this engine), scoring,
save, sound, menus.

## Known-shaky parts, flagged rather than silently assumed
- The **ice mallet** and its wall type: cell types 44/45 are Tibet-exclusive and the
  best guess for an ice version of the breakable wall, but this is unconfirmed --
  we have not found the ice mallet's own pickup id, and 44/45 may turn out to be
  something else entirely (there's a lot of them per level, more consistent with a
  wall texture than a rare object). Check `ICE_WALL_TOOL` in `dr_engine.py`.
- Wall type **9 does not appear in any of the 41 levels** in this jar (only type 8
  does, in Scotland). The break code clearly supports both, so this might just be
  unused in this particular build/region, or reserved for something not in the
  static level data. Worth confirming type 9 shows up somewhere in your own testing
  or reference footage before trusting it's dead code.
- Hookshot pull direction/behavior (teleport-to-adjacent) is a simplification of
  "pulls from up to 2 tiles away" -- the real animation/timing isn't modeled.
- Player animation choices (which strip is "push" vs "walk") are still a best guess.

## Layout
- `gl_sprite.py`  container (.f) and sprite (BSprite) decoder
- `dr_engine.py`  asset loader, level state, physics, tools, dev room, renderer
  (Pillow; display independent)
- `play.py`       pygame window and input
