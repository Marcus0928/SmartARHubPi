# Architecture

## Smart AR HUD — Raspberry Pi Extension

---

## 1. System Diagram

```
Phone (parent repo, Flutter)
   │  ARViewModel.updateAROverlay() fires on each GPS tick
   │  HudBroadcastService serializes state to JSON
   │  sent over Wi-Fi (local socket / WebSocket)
   ▼
Raspberry Pi (this repo)
   │  listener.py — receives JSON, holds latest state in memory
   │  renderer.py — draws arrow + distance from that state
   │  outputs via HDMI (Pygame full-screen window)
   ▼
YG300 driver board (case removed, HDMI on main PCB, USB-C power)
   │  optical projection through close-focus lens stack
   ▼
Combiner (tinted acrylic / reflective film) on dashboard
   │  reflection
   ▼
Driver's eye
```

## 2. Networking design

- **Phone hosts a personal Wi-Fi hotspot.** The Pi connects to it as a saved known network, configured ahead of time (while the Pi still has a monitor/keyboard attached) via `wpa_supplicant`/NetworkManager. The Pi does not host its own hotspot in this design.
- **Transport: a local Wi-Fi socket or WebSocket**, not Bluetooth — chosen for lower overhead on continuous per-second updates and no meaningful payload-size constraint.
- **One-directional:** phone → Pi only. The Pi does not need to send anything back for the current scope.

## 3. Modules (this repo)

### 3.1 `listener.py`
- Opens a socket/WebSocket server and accepts the phone's connection.
- Parses incoming JSON against the data contract in REQUIREMENTS.md.
- Stores the latest valid state in a small shared object that `renderer.py` reads from.
- Handles reconnection gracefully — the phone app may connect/disconnect as navigation starts/stops.
- Runs independently of the render loop (own thread or async event loop) so a slow or stalled connection never blocks drawing.

### 3.2 `renderer.py`
- Opens a full-screen Pygame window sized to the Pi's HDMI output.
- On each frame, reads the latest state from the listener and draws:
  - The arrow shape matching `direction` (same 7 shapes conceptually as the parent app's `DynamicArrowWidget` — chevrons, keep-left/right variants, U-arc, roundabout arc).
  - The `distanceToNextTurn` value as text.
  - Colour selected by `approachStage`.
- Draws against pure black background, content kept within a configurable safe margin from the edges.
- Shows an idle placeholder when no data has been received yet.

### 3.3 `config.py`
- Holds all tunable constants: arrow size, position offsets, font size/family, colour values per approach stage, safe-margin size, window/display resolution.
- Nothing in `renderer.py` should hardcode a number that belongs here.

### 3.4 `main.py`
- Entry point. Starts the listener and the renderer together.

## 4. Why this structure

- Separating `listener.py` from `renderer.py` means a networking hiccup can't freeze the display, and the render loop runs at a steady rate independent of how often new data arrives.
- Centralising tunables in `config.py` matters because the close-focus lens hack (see HARDWARE.md) makes the usable image size and position unknown until physically tested — this needs to be a fast edit-and-rerun loop.
- Keeping this repo's scope strictly to "receive state, draw state" avoids duplicating the parent app's navigation logic, which stays the single source of truth.

## 5. Not yet decided

- Whether Pygame or a lighter-weight approach (raw framebuffer, or an HTML canvas in a kiosk browser) is the better fit — Pygame is the default assumption.
- Exact window/display resolution — depends on close-focus lens testing results.
- Auto-start/systemd service for running headless in the car — not needed during development, while the Pi still has a monitor attached.

---

*Prepared by: Liew Sau Yang | Sunway University | Bachelor of Software Engineering (Hons)*
