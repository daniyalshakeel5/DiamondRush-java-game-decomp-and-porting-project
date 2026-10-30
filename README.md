# Diamond Rush — Nokia N73 desktop rebuild v0.7.0 (Windows launcher, assets supplied by you)

A Windows-playable rebuild of the supplied **240×320 Nokia N73** version. The game logic is compiled from recovered Java source. Graphics, animations, maps, text, and MIDI audio are imported locally from the game archive you select. This package does not execute the original game bytecode.

## New in v0.7.0 — linked doors and failsafes

The editor now supports **pressure plates**, **linked doors**, **gold/silver key locks** and their **key chests**. Set the same **Link channel** (0–15) before painting a trigger and its door. Colored lines show the connections. **Validate** checks the map without saving.

Each channel supports one door controlled by either one pressure plate or up to 15 key locks. Plates open while the player or a boulder holds them; key locks consume matching keys and open after all locks on that channel are unlocked. Use Action to open key chests. These use the original game mechanisms, including closing-door hazards.

Save/load checks reject missing targets, duplicate doors, invalid channels, unsafe placements, incompatible trigger combinations and insufficient keys. Saving preserves the previous file as `.drl.bak`; invalid saves leave the existing file untouched. Custom gameplay/paint failures now produce an error instead of silently continuing. A custom-session watchdog detects an unresponsive game loop after 8 seconds (excluding focus pauses), and loading has a 30-second deadline. These safeguards do not prove puzzle solvability or guarantee recovery from every OS/JVM failure. Campaign saves remain isolated.

Older custom maps remain supported. v0.7.0 also fixes checkpoint numbering and loading-bar initialization in custom play. See EDITOR.md for setup and recovery instructions.

## New in v0.6.0 — Level Editor and Extras

The launcher now has a **Level Editor** page. Create custom Angkor, Scotland or Tibet maps; paint walls, boulders, diamonds, bushes, an entrance, an exit and checkpoints. Save/open `.drl` files, undo strokes, set a diamond requirement and launch a test session. The game's **More games!** menu item is now **Extras**, which lists saved custom levels.

Save in `%LOCALAPPDATA%\DiamondRushN73\custom-levels` (created automatically) to make a level appear in Extras. Each custom play opens a separate game window with temporary saves, leaving campaign progress untouched. Close it to return to the editor or main-menu window. This first version focuses on basic puzzles; bosses, enemies, linked mechanisms and campaign-map importing are not editor features yet. See **EDITOR.md** for controls, validation rules and the file format.

## New in v0.5.0

Open **Display & Audio** in the launcher:

- **Show more of the level** expands the terrain viewport from 240×240 to 384×240: 60% more horizontal terrain. Menus and HUD keep their original size, centered in the wider window.
- **Open texture folder** opens the empty folder created automatically at `%LOCALAPPDATA%\DiamondRushN73\textures`. Extract your PNG sprite sheets there (directly, or in an `upscaled` subfolder). Click **Detect PNGs**, then check **Use upscaled PNG textures**. Uncheck it for stock graphics. Both preferences are saved and apply on the next game launch.

Keep sheet filenames intact, such as `0_0.png` and `gen0_0.png`. The loader supports the project's 16-column, one-pixel-padding sprite-sheet layout at integer scales from 1× through 16×. It uses the original transparency mask to remove the supplied sheets' baked-in background. Logical sprite sizes, hitboxes and game speed remain unchanged. Palette variants without replacement data, missing sheets and incompatible grids use stock graphics.

The supplied `upscaled.rar` has **89 compatible sheets out of 97**. The eight unmatched files are `spl_0`, `ui_1`, `ui_2`, `ui_3`, `ms_0`, `ms_2`, `ms_4`, and `cm_5`; these do not replace the N73 sprites. PNG detection enables the toggle; individual sheets are validated when loaded. The pack is **not bundled** with this asset-free release.

Upscaled rendering uses the launch window scale (1×–4×, default 2×) as its internal pixel density. Larger scales require more rendering work. Changing scale from the running game's menu resizes the window; restart from the launcher to change internal density. The 20 Hz game clock and 60 fps presentation target are unchanged.

Direct Java options, before `-jar`: `-Ddiamond.wideView=true -Ddiamond.upscaled=true -Ddiamond.scale=2`. Override the texture folder with `-Ddiamond.textureDir="path/to/PNG-folder"`.

## Slow-motion fix in v0.4.1

Gameplay now runs at the original N73 loop target of 20 updates per second (50 ms), correcting the earlier 13 Hz setting. Rendering stays at 60 fps. Extract this complete build into a new folder; existing imported assets, saves, and launcher settings are reused automatically.

## Asset-free distribution — v0.3.0

This package contains no original graphics, sound, level files, screenshots, or original game JAR. The launcher lets you select your **Diamond Rush Nokia N73 240×320 JAR**. The launcher verifies and imports 40 required data files, then starts the rebuilt game. A different version is rejected if its resource hashes differ. Repacked JARs with identical resources are accepted. The original JAR's classes are never extracted or executed.

Validated assets are stored under `%LOCALAPPDATA%\DiamondRushN73\assets` on Windows, or `~/DiamondRushN73/assets` on Linux. Later launches reuse this copy. Missing or corrupted assets disable Launch until you import them again. Direct Java startup instead opens the original import dialog. Saves remain separate and unchanged.

You can also select the source explicitly:

```
java -jar DiamondRush-Desktop.jar --game-jar "path/to/original-game.jar"
```

The MIDI patch and world-map freeze fix from v0.2.1 remain included. To retain the prior drum-channel mapping, use `java -Ddiamond.drumChannel=true -jar DiamondRush-Desktop.jar`.

## Timing in this version

Presentation runs at 60 fps, with interpolated sprite positions and camera movement. Original gameplay runs at 20 ticks per second, preserving the duration of physics, hazards, puzzles, animation counters, and menu effects. This is **60 fps rendering, not 60 Hz physics**. Art poses retain their original cadence; no replacement artwork is generated. Interpolation adds approximately one gameplay tick (50 ms) of visual latency. See `TIMING.md` for the timing audit.

## Play on Windows

1. Extract the entire ZIP, including the `launcher` folder.
2. Double-click **Start-Diamond-Rush.bat**. The dashboard opens without Java.
3. If Java is missing, open **Dependencies → Install Java 17**. The launcher downloads a private Eclipse Temurin runtime, verifies SHA-256, and keeps the runtime and its legal notices under your local application-data folder. Administrator access is not required. An internet connection is needed for this step.
4. On **Home**, browse to your original Nokia N73 game JAR and click **Import / repair assets**.
5. Click **Launch Diamond Rush** once the readiness checks pass.

The launcher follows the reference project's sidebar, setup-card, launch-button, and console layout, with original implementation in Windows PowerShell/WPF. It includes saved display/audio preferences, Java detection, an existing-Java picker, runtime installation, asset import/repair, readiness checks, and process logs. See `LAUNCHER.md` for details and test limitations. No Python or Qt installation is required.

The compiled `DiamondRush-Desktop.jar` is included; Python and a compiler are not needed to play. For direct startup without the Windows dashboard: `java -jar DiamondRush-Desktop.jar`. Add `--mute` to disable desktop audio.

| Input | Action |
|---|---|
| Arrow keys / WASD | Move |
| Enter / Space | Action / confirm |
| Q / F1 | Left phone softkey |
| E / Escape | Right phone softkey / back |
| 0–9 or number pad | Original phone number keys |
| F12 | Save a screenshot |

Follow the labels at the bottom of the original screen for softkey actions. The Display menu offers 1×–4× integer pixel scaling and a frame-rate title display. Losing window focus releases held keys and invokes the game's original focus handling.

## Included behavior

All 41 original levels (14 Angkor, 13 Scotland, 14 Tibet), original menus and progression, player and enemy logic, puzzles, tools, bosses, original sprite rendering, 21 MIDI sequences, and the original save-data format are present in the recovered source. Testing coverage is described in `VALIDATION.md`; presence of the source does not constitute an exhaustive playthrough.

Saves persist in `%LOCALAPPDATA%\DiamondRushN73` on Windows. The game's own save/checkpoint and progression rules determine when progress is recorded. Screenshots go to your user folder under `Pictures\DiamondRushN73`.

## Fidelity status

The comparison harness runs the supplied JAR and rebuilt source against the same desktop graphics/input implementation, a fixed clock, and identical button presses. It compares every 240×320 framebuffer and 457 internal game fields. See `validation/REPORT.json` for the measured results.

Remaining validation: complete playthroughs, every secret and boss outcome, long-term progression and save recovery, physical Nokia display/audio comparison, and an actual Windows UI/audio test. MIDI uses the desktop synthesizer, so instrument timbre can differ from the phone. Phone vibration and external promotional links have no desktop effect. Desktop display scaling and keyboard mapping are host features.

## Build from source

Use a **JDK 17+**:

- Windows: run `Build-Windows.bat` (requires `javac` and `jar` on PATH).
- With Python 3.10+: run `python build.py`.

The generated classes target Java 8 bytecode. Java 17 is the documented and tested Java version. No Maven dependencies, emulator installation, or network connection are required at runtime. The original game JAR is required for the first asset import.

## Repeat the original/rebuild comparison

With Python 3.10+ and JDK 17+, run:

```
python tests/run_compare.py "path/to/the-original-N73.jar"
```

This requires the exact input JAR identified by `ASSET-MANIFEST.json`. Test-only instrumentation substitutes the clock, disables the autonomous game thread, and supplies memory-backed application resources. The game update and draw methods are then invoked directly. It does not change game rules or image data. These substitutions are absent from the distributed application.

## Project layout

- `src/class_*.java`, `src/GloftDIRU.java`: recovered and corrected game source.
- `src/DesktopLauncher.java`: Swing window and keyboard host.
- `src/javax/microedition/`: small desktop implementations of APIs used by this game.
- `src/GameResources.java`: memory-backed loading of original resources.
- `src/desktop/assets/`: first-run import, cache validation, and resource loading.
- `package.py`: asset-free distribution builder with archive checks.
- `tests/`: deterministic differential harness and desktop API checks.
- `ASSET-MANIFEST.json`: source archive hash, individual resource hashes, and all map-plane hashes.
- `PROVENANCE.md`: research references and source recovery details.
