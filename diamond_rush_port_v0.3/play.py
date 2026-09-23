"""
Diamond Rush (Gameloft J2ME v1.0.9) -- pygame front-end for dr_engine.

    pip install pygame pillow
    python play.py [path/to/your/DiamondRush.jar]

You must supply your own copy of the game jar; nothing from the game is bundled.

Controls: arrows/WASD move (tap to turn, tap again to step, hold to walk) -
SPACE use tool (hammer/ice mallet on an adjacent breakable wall, else hookshot
on the nearest boulder/gem within 2 tiles) - F1 dev room (every object id in
the current world, all tools granted; press again to cycle worlds) - F5 back
to the real level - R restart - [ ] previous/next level - 1/2/3 jump to world
- TAB toggle debug id boxes - Enter next level after finishing - Esc quit.
"""
import glob
import sys

import pygame

from dr_engine import Assets, Game, VW, VH

SCALE = 3
FPS = 30

KEYMAP = {pygame.K_LEFT: 'left', pygame.K_a: 'left', pygame.K_UP: 'up', pygame.K_w: 'up',
          pygame.K_RIGHT: 'right', pygame.K_d: 'right', pygame.K_DOWN: 'down', pygame.K_s: 'down'}


def find_jar():
    if len(sys.argv) > 1:
        return sys.argv[1]
    jars = glob.glob('*.jar')
    if jars:
        return jars[0]
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw()
        path = filedialog.askopenfilename(title='Select your Diamond Rush .jar (Gameloft v1.0.9)',
                                          filetypes=[('Java archive', '*.jar')])
        root.destroy()
        if path:
            return path
    except Exception:
        pass
    print(__doc__)
    sys.exit(1)


def main():
    assets = Assets(find_jar())
    game = Game(assets, 0, 0)
    pygame.init()
    screen = pygame.display.set_mode((VW * SCALE, VH * SCALE))
    pygame.display.set_caption('Diamond Rush (port)')
    clock = pygame.time.Clock()
    pressed = []                      # keys currently held, most recent last
    action = False                    # tool-use, consumed one tick after a keydown
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in KEYMAP:
                    if ev.key in pressed: pressed.remove(ev.key)
                    pressed.append(ev.key)
                elif ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r:
                    game.restart()
                elif ev.key == pygame.K_TAB:
                    game.debug = not game.debug
                elif ev.key == pygame.K_SPACE:
                    action = True     # hammer/ice-mallet/hookshot, whichever applies (see dr_engine.Game.use)
                elif ev.key == pygame.K_F1:
                    # dev room: one of every object id in the current world, all tools granted.
                    # F1 again cycles to the next world's dev room (different reskins/ids per world).
                    w = game.world if not getattr(game, 'devroom_ids', None) else (game.world + 1) % 3
                    ids = game.load_devroom(world=w)
                    print(f'[dev room] world {w+1}, ids present: {ids}')
                elif ev.key == pygame.K_F5:
                    game.load(game.world, game.level)      # leave the dev room, back to a real level
                elif ev.key == pygame.K_RIGHTBRACKET or (ev.key == pygame.K_RETURN and game.state == 'won'):
                    game.goto(game.world, game.level + 1)
                elif ev.key == pygame.K_LEFTBRACKET:
                    game.goto(game.world, game.level - 1)
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    game.goto(ev.key - pygame.K_1, 0)
            elif ev.type == pygame.KEYUP and ev.key in pressed:
                pressed.remove(ev.key)
        held = KEYMAP[pressed[-1]] if pressed else None
        game.update(held, action)
        action = False
        img = game.render()
        surf = pygame.image.frombuffer(img.tobytes(), img.size, 'RGB')
        screen.blit(pygame.transform.scale(surf, screen.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
