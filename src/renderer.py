"""Minimal static render test (Task 2).

Opens a full-screen black window and draws a single green forward chevron in
the centre of the safe area. No networking yet — this only validates the
Pi -> HDMI -> YG300 output path.

Run with:  python3 renderer.py   (press Esc or Q to quit)
"""

import pygame

import config


def get_safe_rect(screen_size):
    """Return the centred content area, inset from every edge by the safe margin."""
    width, height = screen_size
    margin_x = int(width * config.SAFE_MARGIN_FRACTION)
    margin_y = int(height * config.SAFE_MARGIN_FRACTION)
    return pygame.Rect(margin_x, margin_y, width - 2 * margin_x, height - 2 * margin_y)


def forward_chevron_points(center, size, thickness):
    """Points for an upward-pointing chevron of the given size, centred on `center`."""
    cx, cy = center
    half = size / 2
    return [
        (cx, cy - half),                    # outer apex
        (cx + half, cy + half - thickness),  # right tip, top edge
        (cx + half, cy + half),              # right tip, bottom edge
        (cx, cy - half + thickness),         # inner apex
        (cx - half, cy + half),              # left tip, bottom edge
        (cx - half, cy + half - thickness),  # left tip, top edge
    ]


def draw_frame(screen):
    screen.fill(config.BACKGROUND_COLOUR)

    safe = get_safe_rect(screen.get_size())
    size = min(safe.width, safe.height) * config.ARROW_SIZE_FRACTION
    thickness = size * config.ARROW_THICKNESS_FRACTION
    center = (safe.centerx + config.ARROW_OFFSET_X, safe.centery + config.ARROW_OFFSET_Y)

    pygame.draw.polygon(screen, config.ARROW_COLOUR, forward_chevron_points(center, size, thickness))


def run():
    pygame.init()
    if config.FULLSCREEN:
        screen = pygame.display.set_mode(config.FULLSCREEN_SIZE, pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(config.WINDOWED_SIZE)
    pygame.display.set_caption("Smart AR HUD")
    pygame.mouse.set_visible(not config.HIDE_MOUSE_CURSOR)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

        draw_frame(screen)
        pygame.display.flip()
        clock.tick(config.FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
