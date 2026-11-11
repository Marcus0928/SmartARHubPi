"""All tunable constants for the HUD renderer.

Edit values here during physical lens/combiner testing — nothing in the
renderer should hardcode a size, offset, or colour.
"""

# --- Display ---------------------------------------------------------------
# Fullscreen on the Pi's HDMI output. Pass --windowed on the command line to
# preview in a window on a dev PC instead.
FULLSCREEN = True
# (0, 0) lets Pygame use the display's current native resolution in fullscreen.
FULLSCREEN_SIZE = (0, 0)
WINDOWED_SIZE = (800, 480)
FPS = 30
HIDE_MOUSE_CURSOR = True

# --- Colours (R, G, B) -----------------------------------------------------
# Solid colours on pure black only: the YG300 is dim, so translucency or glow
# just reads as a dimmer arrow.
BACKGROUND_COLOUR = (0, 0, 0)
# Arrow colour per approach stage (matches the parent app's tiers).
STAGE_COLOURS = {
    "far": (0x00, 0xE6, 0x76),          # #00E676
    "approaching": (0xFF, 0xC1, 0x07),  # #FFC107
    "imminent": (0xFF, 0x52, 0x52),     # #FF5252
}
LABEL_COLOUR = (255, 255, 255)
EXIT_NUMBER_COLOUR = (255, 255, 255)

# --- Safe area -------------------------------------------------------------
# Fraction of each screen dimension kept clear at every edge, to tolerate
# vignetting/softness from the close-focus lens stack.
SAFE_MARGIN_FRACTION = 0.15

# --- Arrow layout ----------------------------------------------------------
# Arrow box (square) size as a fraction of the safe area's shorter side.
ARROW_SIZE_FRACTION = 0.6
# Pixel offset of the arrow + label group from the safe area's centre (+x right, +y down).
ARROW_OFFSET_X = 0
ARROW_OFFSET_Y = 0
# Each arrow part is drawn at this multiple of its final size, then
# smoothscaled down so edges come out anti-aliased.
ARROW_SUPERSAMPLE = 4
# Segments used to approximate the roundabout arc.
ROUNDABOUT_ARC_SEGMENTS = 72

# --- Arrow geometry --------------------------------------------------------
# Mirrors DynamicArrowWidget's _ArrowPainter. Its coordinates are on a
# 120-unit square (scale = width / 120): "_FRACTION" values are fractions of the
# box side, "_UNITS" values (strokes, offsets) are in those 120ths.
ARROW_DESIGN_UNITS = 120.0

# Shared chevron shape (forward/left/right): a flat "^".
CHEVRON_HALF_WIDTH_FRACTION = 0.38
CHEVRON_ARM_HEIGHT_FRACTION = 0.14

# forward / left / right: stacked chevrons, evenly spaced (1/4, 2/4, 3/4 for 3).
TURN_CHEVRON_COUNT = 3
TURN_STROKE_UNITS = 12.0

# keepLeft / keepRight: 6 smaller chevrons drifting and rotating to the side.
# Tables run bottom -> top; keepLeft is the horizontal mirror.
KEEP_HALF_WIDTH_FACTOR = 0.4          # times CHEVRON_HALF_WIDTH_FRACTION
KEEP_STROKE_UNITS = 8.0
KEEP_ROTATIONS_DEG = (9.0, 12.0, 25.0, 40.0, 55.0, 68.0)
KEEP_X_OFFSETS_UNITS = (4.0, 10.0, 22.0, 38.0, 56.0, 76.0)

# uTurn: small chevrons along a U (up the left stem, over, down the right).
UTURN_CHEVRON_COUNT = 15
UTURN_RADIUS_FRACTION = 0.225
UTURN_TOP_FRACTION = 0.10             # top of the arc, from the box top
UTURN_STEM_BOTTOM_FRACTION = 0.88
UTURN_HALF_WIDTH_FACTOR = 0.2         # times CHEVRON_HALF_WIDTH_FRACTION
UTURN_ARM_HEIGHT_FRACTION = 0.07
UTURN_STROKE_UNITS = 6.0

# roundabout: 270-degree clockwise arc, gap at the bottom, fixed 45-degree exit.
# Angles are screen angles (0 = right, clockwise positive).
ROUNDABOUT_RADIUS_FRACTION = 0.33
ROUNDABOUT_STROKE_UNITS = 14.0
ROUNDABOUT_START_DEG = 135.0
ROUNDABOUT_SWEEP_DEG = 270.0
ROUNDABOUT_ENTRY_LENGTH_UNITS = 15.0
ROUNDABOUT_EXIT_STEM_UNITS = 6.0
ROUNDABOUT_EXIT_HEAD_LENGTH_UNITS = 14.0
ROUNDABOUT_EXIT_HEAD_HALF_WIDTH_UNITS = 9.0
EXIT_NUMBER_FONT_FRACTION = 0.3       # 36 / 120

# --- Flow wave -------------------------------------------------------------
# A brightness wave sweeps through the chevrons (bottom -> top, or along the
# turn). Each chevron snaps to one of these solid brightness levels, dimmest
# first; keep the minimum high enough to stay visible through the projector.
FLOW_BRIGHTNESS_LEVELS = (0.4, 0.6, 0.8, 1.0)
FLOW_PERIOD_MS = 1000
UTURN_FLOW_PERIOD_MS = 5000           # 15 chevrons, same per-chevron rate

# --- Label -----------------------------------------------------------------
# None = Pygame's built-in bold sans font.
LABEL_FONT_NAME = None
LABEL_FONT_FRACTION = 0.1             # of the arrow box (18 px on a 180 px box)
LABEL_GAP_FRACTION = 0.045            # gap between arrow box and label (8 / 180)
TURN_NOW_DISTANCE_M = 50

# --- Network listener ------------------------------------------------------
# UDP address the phone sends JSON packets to ("0.0.0.0" = all interfaces).
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 5005
LISTEN_MAX_PACKET_BYTES = 4096
# Blank the screen if no valid packet has arrived for this many seconds.
STALE_TIMEOUT_S = 5.0

# --- Dev controls ----------------------------------------------------------
# Sample distance (metres) used for each approach stage when cycling with Up/Down.
DEV_STAGE_DISTANCES_M = {
    "far": 500,
    "approaching": 120,
    "imminent": 30,
}
DEV_DEFAULT_EXIT_NUMBER = 1
