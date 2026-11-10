"""HUD renderer: turn arrow + distance label (Tasks 3 and 4).

Arrow shapes mirror the parent app's DynamicArrowWidget (_ArrowPainter), adapted
for the dim YG300 projector: solid colours on pure black, no glow or
translucency, and the flowing opacity wave replaced by stepped brightness.

Each arrow part is rasterised once as a white mask at ARROW_SUPERSAMPLE x size,
smoothscaled down (anti-aliased edges), cached, and re-tinted per frame.

Run:  python renderer.py [--windowed]

Dev keys (temporary test aid, Task 3):
    Left / Right   cycle the 7 directions
    Up / Down      cycle approach stage (far / approaching / imminent)
    1 - 4          roundabout exit number
    Esc / Q        quit
"""

import argparse
import math

import pygame

import config

DIRECTIONS = ("forward", "left", "right", "keepLeft", "keepRight", "uTurn", "roundabout")
STAGES = ("far", "approaching", "imminent")

_MASK_WHITE = (255, 255, 255)
_MASK_BLACK = (0, 0, 0)


# --- Geometry (design units: a ARROW_DESIGN_UNITS square, y down) ------------

class Piece:
    """One separately tinted part of an arrow.

    strokes: list of (points, width_units) drawn as round-capped polylines.
    fills:   list of polygons drawn filled.
    flow_index: position in the flow wave, or None for constant full brightness.
    """

    def __init__(self, strokes=(), fills=(), flow_index=None):
        self.strokes = list(strokes)
        self.fills = list(fills)
        self.flow_index = flow_index

    def map_points(self, fn):
        return Piece(
            [([fn(p) for p in pts], w) for pts, w in self.strokes],
            [[fn(p) for p in pts] for pts in self.fills],
            self.flow_index,
        )


class ArrowShape:
    def __init__(self, pieces, flow_count=0, flow_period_ms=config.FLOW_PERIOD_MS):
        self.pieces = pieces
        self.flow_count = flow_count
        self.flow_period_ms = flow_period_ms


def _chevron(half_w, arm_h):
    """A '^' centred on the origin, apex up."""
    return [(-half_w, arm_h / 2), (0.0, -arm_h / 2), (half_w, arm_h / 2)]


def _place(points, angle, x, y):
    """Rotate points about the origin by `angle` (clockwise on screen), then move to (x, y)."""
    c, s = math.cos(angle), math.sin(angle)
    return [(x + px * c - py * s, y + px * s + py * c) for px, py in points]


def _rotate_about_centre(shape, angle):
    centre = config.ARROW_DESIGN_UNITS / 2
    c, s = math.cos(angle), math.sin(angle)

    def fn(p):
        dx, dy = p[0] - centre, p[1] - centre
        return (centre + dx * c - dy * s, centre + dx * s + dy * c)

    return ArrowShape([pc.map_points(fn) for pc in shape.pieces], shape.flow_count, shape.flow_period_ms)


def _mirror(shape):
    units = config.ARROW_DESIGN_UNITS
    pieces = [pc.map_points(lambda p: (units - p[0], p[1])) for pc in shape.pieces]
    return ArrowShape(pieces, shape.flow_count, shape.flow_period_ms)


def _forward_shape():
    u = config.ARROW_DESIGN_UNITS
    n = config.TURN_CHEVRON_COUNT
    chevron = _chevron(u * config.CHEVRON_HALF_WIDTH_FRACTION, u * config.CHEVRON_ARM_HEIGHT_FRACTION)
    pieces = []
    for canvas_idx in range(n):  # 0 = top (leading) chevron
        cy = u / (n + 1) * (canvas_idx + 1)
        pts = _place(chevron, 0.0, u / 2, cy)
        pieces.append(Piece([(pts, config.TURN_STROKE_UNITS)], flow_index=n - 1 - canvas_idx))
    return ArrowShape(pieces, n)


def _keep_right_shape():
    u = config.ARROW_DESIGN_UNITS
    rotations = config.KEEP_ROTATIONS_DEG
    offsets = config.KEEP_X_OFFSETS_UNITS
    n = len(rotations)
    if len(offsets) != n:
        raise ValueError("KEEP_ROTATIONS_DEG and KEEP_X_OFFSETS_UNITS must be the same length")
    chevron = _chevron(
        u * config.CHEVRON_HALF_WIDTH_FRACTION * config.KEEP_HALF_WIDTH_FACTOR,
        u * config.CHEVRON_ARM_HEIGHT_FRACTION,
    )
    pieces = []
    for canvas_idx in range(n):  # 0 = top slot
        cy = u / n * canvas_idx + u / (2 * n)
        flow_idx = n - 1 - canvas_idx  # tables are indexed bottom -> top
        pts = _place(chevron, math.radians(rotations[flow_idx]), u / 2 + offsets[flow_idx], cy)
        pieces.append(Piece([(pts, config.KEEP_STROKE_UNITS)], flow_index=flow_idx))
    return ArrowShape(pieces, n)


def _uturn_shape():
    u = config.ARROW_DESIGN_UNITS
    n = config.UTURN_CHEVRON_COUNT
    cx = u / 2
    r = u * config.UTURN_RADIUS_FRACTION
    top_y = u * config.UTURN_TOP_FRACTION + r          # arc centre y
    stem_bottom = u * config.UTURN_STEM_BOTTOM_FRACTION
    chevron = _chevron(
        u * config.CHEVRON_HALF_WIDTH_FRACTION * config.UTURN_HALF_WIDTH_FACTOR,
        u * config.UTURN_ARM_HEIGHT_FRACTION,
    )

    stem_len = stem_bottom - top_y
    arc_len = math.pi * r
    total_len = 2 * stem_len + arc_len

    pieces = []
    for i in range(n):
        d = total_len * i / (n - 1)
        if d <= stem_len:                       # up the left stem
            px, py, tangent = cx - r, stem_bottom - d, -math.pi / 2
        elif d <= stem_len + arc_len:           # over the top
            theta = math.pi + (d - stem_len) / arc_len * math.pi
            px = cx + r * math.cos(theta)
            py = top_y + r * math.sin(theta)
            tangent = math.atan2(math.cos(theta), -math.sin(theta))
        else:                                   # down the right stem
            px, py, tangent = cx + r, top_y + (d - stem_len - arc_len), math.pi / 2
        pts = _place(chevron, tangent + math.pi / 2, px, py)
        pieces.append(Piece([(pts, config.UTURN_STROKE_UNITS)], flow_index=i))
    return ArrowShape(pieces, n, config.UTURN_FLOW_PERIOD_MS)


def _roundabout_shape():
    u = config.ARROW_DESIGN_UNITS
    c = u / 2
    r = u * config.ROUNDABOUT_RADIUS_FRACTION
    stroke = config.ROUNDABOUT_STROKE_UNITS
    start = math.radians(config.ROUNDABOUT_START_DEG)
    end = start + math.radians(config.ROUNDABOUT_SWEEP_DEG)

    def polar(angle, radius):
        return (c + radius * math.cos(angle), c + radius * math.sin(angle))

    segs = config.ROUNDABOUT_ARC_SEGMENTS
    arc = [polar(start + (end - start) * i / segs, r) for i in range(segs + 1)]
    entry = [polar(start, r + config.ROUNDABOUT_ENTRY_LENGTH_UNITS), polar(start, r)]

    stem_end_r = r + config.ROUNDABOUT_EXIT_STEM_UNITS
    exit_stem = [polar(end, r), polar(end, stem_end_r)]
    base_x, base_y = polar(end, stem_end_r)
    tip = polar(end, stem_end_r + config.ROUNDABOUT_EXIT_HEAD_LENGTH_UNITS)
    hw = config.ROUNDABOUT_EXIT_HEAD_HALF_WIDTH_UNITS
    perp_x, perp_y = -math.sin(end), math.cos(end)
    head = [
        tip,
        (base_x + perp_x * hw, base_y + perp_y * hw),
        (base_x - perp_x * hw, base_y - perp_y * hw),
    ]
    piece = Piece([(arc, stroke), (entry, stroke), (exit_stem, stroke)], [head])
    return ArrowShape([piece])


def build_shape(direction):
    if direction == "forward":
        return _forward_shape()
    if direction == "right":
        return _rotate_about_centre(_forward_shape(), math.pi / 2)
    if direction == "left":
        return _mirror(_rotate_about_centre(_forward_shape(), math.pi / 2))
    if direction == "keepRight":
        return _keep_right_shape()
    if direction == "keepLeft":
        return _mirror(_keep_right_shape())
    if direction == "uTurn":
        return _uturn_shape()
    if direction == "roundabout":
        return _roundabout_shape()
    raise ValueError(f"Unknown direction: {direction!r}")


# --- Rasterising -------------------------------------------------------------

def _draw_round_polyline(surface, points, width):
    """Thick polyline with round caps and joins (quads + a disc at every vertex)."""
    radius = width / 2
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        length = math.hypot(bx - ax, by - ay)
        if length == 0:
            continue
        nx, ny = -(by - ay) / length * radius, (bx - ax) / length * radius
        pygame.draw.polygon(
            surface, _MASK_WHITE,
            [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)],
        )
    for x, y in points:
        pygame.draw.circle(surface, _MASK_WHITE, (round(x), round(y)), round(radius))


def _rasterise_piece(piece, px_per_unit):
    """Return (mask_surface, (x, y) offset within the arrow box) for one piece."""
    ss = config.ARROW_SUPERSAMPLE
    xs, ys = [], []
    for pts, width in piece.strokes:
        pad = width / 2
        xs += [p[0] - pad for p in pts] + [p[0] + pad for p in pts]
        ys += [p[1] - pad for p in pts] + [p[1] + pad for p in pts]
    for pts in piece.fills:
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]

    left = math.floor(min(xs) * px_per_unit) - 1
    top = math.floor(min(ys) * px_per_unit) - 1
    w = math.ceil(max(xs) * px_per_unit) + 1 - left
    h = math.ceil(max(ys) * px_per_unit) + 1 - top

    big = pygame.Surface((w * ss, h * ss))
    big.fill(_MASK_BLACK)

    def to_big(p):
        return ((p[0] * px_per_unit - left) * ss, (p[1] * px_per_unit - top) * ss)

    for pts, width in piece.strokes:
        _draw_round_polyline(big, [to_big(p) for p in pts], width * px_per_unit * ss)
    for pts in piece.fills:
        pygame.draw.polygon(big, _MASK_WHITE, [to_big(p) for p in pts])

    return pygame.transform.smoothscale(big, (w, h)), (left, top)


def _flow_brightness(flow_index, count, t):
    """Stepped version of the Flutter flow wave (t in [0, 1))."""
    if flow_index is None or count == 0:
        return 1.0
    half = count / 2
    dist = abs(t * count - flow_index)
    if dist > half:
        dist = count - dist
    v = max(0.0, 1.0 - dist / half)
    levels = config.FLOW_BRIGHTNESS_LEVELS
    return levels[min(int(v * len(levels)), len(levels) - 1)]


# --- Label text ----------------------------------------------------------------

def format_distance(metres):
    """Metric rules from the parent app's formatDistance()."""
    if metres >= 1000:
        return f"{metres / 1000:.1f} km"
    rounded = int(math.floor(metres / 10 + 0.5)) * 10   # Dart round(): half away from zero
    return f"{min(max(rounded, 10), 990)} m"


def label_text(direction, distance_m, exit_number):
    if direction == "roundabout":
        return f"Take Exit {exit_number}" if exit_number is not None else "Take the Exit"
    if distance_m < config.TURN_NOW_DISTANCE_M:
        return "Turn now!"
    return f"In {format_distance(distance_m)}"


# --- Renderer ------------------------------------------------------------------

class HudRenderer:
    def __init__(self):
        self._masks = {}   # (direction, box_px) -> (ArrowShape, [(mask, offset), ...])
        self._tinted = {}  # (direction, box_px, piece_idx, rgb) -> Surface
        self._fonts = {}   # px size -> Font

    def _font(self, size):
        size = max(1, int(size))
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(config.LABEL_FONT_NAME, size)
        return self._fonts[size]

    def _arrow(self, direction, box_px):
        key = (direction, box_px)
        if key not in self._masks:
            shape = build_shape(direction)
            ppu = box_px / config.ARROW_DESIGN_UNITS
            self._masks[key] = (shape, [_rasterise_piece(pc, ppu) for pc in shape.pieces])
        return self._masks[key]

    def _tint(self, key, mask, rgb):
        surf = self._tinted.get(key)
        if surf is None:
            surf = mask.copy()
            surf.fill(rgb, special_flags=pygame.BLEND_RGB_MULT)
            self._tinted[key] = surf
        return surf

    def draw(self, screen, direction, distance_m, stage, exit_number=None, now_ms=None):
        if now_ms is None:
            now_ms = pygame.time.get_ticks()
        screen.fill(config.BACKGROUND_COLOUR)

        safe = get_safe_rect(screen.get_size())
        box_px = int(min(safe.width, safe.height) * config.ARROW_SIZE_FRACTION)
        font = self._font(box_px * config.LABEL_FONT_FRACTION)
        gap = round(box_px * config.LABEL_GAP_FRACTION)
        group_h = box_px + gap + font.get_height()

        box = pygame.Rect(0, 0, box_px, box_px)
        box.centerx = safe.centerx + config.ARROW_OFFSET_X
        box.top = safe.centery - group_h // 2 + config.ARROW_OFFSET_Y

        # Arrow
        colour = config.STAGE_COLOURS[stage]
        shape, masks = self._arrow(direction, box_px)
        t = (now_ms % shape.flow_period_ms) / shape.flow_period_ms
        for idx, (piece, (mask, (ox, oy))) in enumerate(zip(shape.pieces, masks)):
            level = _flow_brightness(piece.flow_index, shape.flow_count, t)
            rgb = tuple(int(ch * level + 0.5) for ch in colour)
            surf = self._tint((direction, box_px, idx, rgb), mask, rgb)
            screen.blit(surf, (box.x + ox, box.y + oy), special_flags=pygame.BLEND_RGB_MAX)

        # Roundabout exit number, centred in the circle
        if direction == "roundabout" and exit_number is not None:
            num_font = self._font(box_px * config.EXIT_NUMBER_FONT_FRACTION)
            num = num_font.render(str(exit_number), True, config.EXIT_NUMBER_COLOUR,
                                  config.BACKGROUND_COLOUR)
            screen.blit(num, num.get_rect(center=box.center))

        # Label, straight on black (no pill)
        text = font.render(label_text(direction, distance_m, exit_number), True,
                           config.LABEL_COLOUR, config.BACKGROUND_COLOUR)
        screen.blit(text, text.get_rect(midtop=(box.centerx, box.bottom + gap)))


def get_safe_rect(screen_size):
    """Return the centred content area, inset from every edge by the safe margin."""
    width, height = screen_size
    margin_x = int(width * config.SAFE_MARGIN_FRACTION)
    margin_y = int(height * config.SAFE_MARGIN_FRACTION)
    return pygame.Rect(margin_x, margin_y, width - 2 * margin_x, height - 2 * margin_y)


# --- Dev loop ----------------------------------------------------------------

_EXIT_KEYS = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4}


def run(windowed=False):
    pygame.init()
    if config.FULLSCREEN and not windowed:
        screen = pygame.display.set_mode(config.FULLSCREEN_SIZE, pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(config.WINDOWED_SIZE)
    pygame.display.set_caption("Smart AR HUD")
    pygame.mouse.set_visible(not config.HIDE_MOUSE_CURSOR)
    clock = pygame.time.Clock()
    hud = HudRenderer()

    direction_idx = 0
    stage_idx = 0
    exit_number = config.DEV_DEFAULT_EXIT_NUMBER

    def report():
        print(f"[dev] direction={DIRECTIONS[direction_idx]} stage={STAGES[stage_idx]} "
              f"distance={config.DEV_STAGE_DISTANCES_M[STAGES[stage_idx]]}m exit={exit_number}")

    report()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                    continue
                if event.key == pygame.K_RIGHT:
                    direction_idx = (direction_idx + 1) % len(DIRECTIONS)
                elif event.key == pygame.K_LEFT:
                    direction_idx = (direction_idx - 1) % len(DIRECTIONS)
                elif event.key == pygame.K_UP:
                    stage_idx = (stage_idx + 1) % len(STAGES)
                elif event.key == pygame.K_DOWN:
                    stage_idx = (stage_idx - 1) % len(STAGES)
                elif event.key in _EXIT_KEYS:
                    exit_number = _EXIT_KEYS[event.key]
                else:
                    continue
                report()

        stage = STAGES[stage_idx]
        hud.draw(screen, DIRECTIONS[direction_idx], config.DEV_STAGE_DISTANCES_M[stage],
                 stage, exit_number)
        pygame.display.flip()
        clock.tick(config.FPS)

    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart AR HUD renderer")
    parser.add_argument("--windowed", action="store_true",
                        help="open in a window (WINDOWED_SIZE) instead of fullscreen")
    run(windowed=parser.parse_args().windowed)
