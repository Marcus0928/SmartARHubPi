"""Entry point: UDP and/or BLE listener + HUD renderer (Task 6).

Run:
    python main.py                    live mode, fullscreen, UDP + BLE
    python main.py --transport udp    UDP only (no Bluetooth needed, e.g. on a dev PC)
    python main.py --transport ble    BLE only
    python main.py --windowed         live mode in a window
    python main.py --demo             keyboard dev mode (no phone needed; see renderer.py for keys)

In live mode the HUD shows the latest packet from either transport. Until the
first packet arrives, or if none has arrived for STALE_TIMEOUT_S, the screen
is blank black. Esc / Q quits.

With --transport both, if one transport fails to start (e.g. no Bluetooth
adapter, or bless not installed) a warning is printed and the HUD runs on the
other. With a single transport, a failure to start is an error.
"""

import argparse
import time

import pygame

import config
from listener import LatestState, Listener
from renderer import HudRenderer, run as run_demo


def _start_udp(store):
    listener = Listener(store=store).start()
    print(f"[live] listening for UDP on {config.LISTEN_HOST}:{config.LISTEN_PORT}")
    return listener


def _start_ble(store):
    from ble_listener import BleListener  # imported lazily: needs bless + BlueZ

    listener = BleListener(store=store).start()
    print(f"[live] advertising BLE as {config.BLE_DEVICE_NAME!r}, service {config.BLE_SERVICE_UUID}")
    return listener


def start_listeners(transport):
    """Start the requested transports, all feeding one shared LatestState."""
    store = LatestState()
    starters = {"udp": _start_udp, "ble": _start_ble}
    names = ("udp", "ble") if transport == "both" else (transport,)
    listeners = []
    for name in names:
        try:
            listeners.append(starters[name](store))
        except Exception as exc:
            if transport != "both":
                raise
            print(f"[live] warning: {name.upper()} transport unavailable: {exc}")
    if not listeners:
        raise RuntimeError("no transport could be started")
    return store, listeners


def run_live(windowed=False, transport="both"):
    store, listeners = start_listeners(transport)

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

            state = store.latest()
            if state is None or time.monotonic() - state.received_at > config.STALE_TIMEOUT_S:
                screen.fill(config.BACKGROUND_COLOUR)
            else:
                hud.draw(screen, state.direction, state.distance_m, state.stage, state.exit_number)
            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        for listener in listeners:
            listener.stop()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Smart AR HUD")
    parser.add_argument("--windowed", action="store_true",
                        help="open in a window (WINDOWED_SIZE) instead of fullscreen")
    parser.add_argument("--demo", action="store_true",
                        help="keyboard dev mode: cycle shapes/stages without the phone")
    parser.add_argument("--transport", choices=("udp", "ble", "both"), default="both",
                        help="how the phone's packets arrive (default: both)")
    args = parser.parse_args()
    if args.demo:
        run_demo(windowed=args.windowed)
    else:
        run_live(windowed=args.windowed, transport=args.transport)


if __name__ == "__main__":
    main()
