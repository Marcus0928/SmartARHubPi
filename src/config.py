"""All tunable constants for the HUD renderer.

Edit values here during physical lens/combiner testing — nothing in the
renderer should hardcode a size, offset, or colour.
"""

# --- Display ---------------------------------------------------------------
# Fullscreen on the Pi's HDMI output. Set False to test in a window on a dev PC.
FULLSCREEN = True
# (0, 0) lets Pygame use the display's current native resolution in fullscreen.
FULLSCREEN_SIZE = (0, 0)
WINDOWED_SIZE = (800, 480)
FPS = 30
HIDE_MOUSE_CURSOR = True

# --- Colours (R, G, B) -----------------------------------------------------
BACKGROUND_COLOUR = (0, 0, 0)
ARROW_COLOUR = (0, 200, 0)

# --- Safe area -------------------------------------------------------------
# Fraction of each screen dimension kept clear at every edge, to tolerate
# vignetting/softness from the close-focus lens stack.
SAFE_MARGIN_FRACTION = 0.15

# --- Arrow -----------------------------------------------------------------
# Arrow size as a fraction of the safe area's shorter side.
ARROW_SIZE_FRACTION = 0.6
# Chevron stroke thickness as a fraction of the arrow size.
ARROW_THICKNESS_FRACTION = 0.25
# Pixel offset of the arrow centre from the safe area's centre (+x right, +y down).
ARROW_OFFSET_X = 0
ARROW_OFFSET_Y = 0
