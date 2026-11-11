"""Entry point: UDP listener + HUD renderer (Task 6).

Run:
    python main.py              live mode, fullscreen
    python main.py --windowed   live mode in a window
    python main.py --demo       keyboard dev mode (no phone needed; see renderer.py for keys)

In live mode the HUD shows the latest packet from the phone. Until the first
packet arrives, or if none has arrived for STALE_TIMEOUT_S, the screen is
blank black. Esc / Q quits.
"""

import argparse
import time

import pygame

import config
from listener import Listener
from renderer import HudRenderer, run as run_demo


def run_live(windowed=False):
    listener = Listener().start()
    print(f"[live] listening for UDP on {config.LISTEN_HOST}:{config.LISTEN_PORT}")

    pygame.init()
    if config.FULLSCREEN and not windowed:
        screen = pygame.display.set_mode(config.FULLSCREEN_SIZE, pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(config.WINDOWED_SIZE)
    pygame.display.set_caption("Smart AR HUD")
    pygame.mouse.set_visible(not config.HIDE_MOUSE_CURSOR)
    clock = pygame.time.Clock()
    hud = HudRenderer()

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

            state = listener.latest()
            if state is None or time.monotonic() - state.received_at > config.STALE_TIMEOUT_S:
                screen.fill(config.BACKGROUND_COLOUR)
            else:
                hud.draw(screen, state.direction, state.distance_m, state.stage, state.exit_number)
            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        listener.stop()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Smart AR HUD")
    parser.add_argument("--windowed", action="store_true",
                        help="open in a window (WINDOWED_SIZE) instead of fullscreen")
    parser.add_argument("--demo", action="store_true",
                        help="keyboard dev mode: cycle shapes/stages without the phone")
    args = parser.parse_args()
    if args.demo:
        run_demo(windowed=args.windowed)
    else:
        run_live(windowed=args.windowed)


if __name__ == "__main__":
    main()
