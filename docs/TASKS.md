# Implementation Tasks

## Smart AR HUD — Raspberry Pi Extension

For Claude Code to work through in order. Each task should be completed and confirmed working before moving to the next — this project depends on physical hardware testing between software steps, so don't assume a step works until it has been run on the actual Pi.

---

### Task 1 — Environment check
Confirm Python 3 and Pygame are available on the Pi. If Pygame is missing, install it. Report back exact versions found.

### Task 2 — Minimal static render test
Write a minimal `renderer.py` that opens a full-screen black Pygame window and draws a single static forward-arrow shape in the centre, in green, with no networking involved yet. Purpose: validate the HDMI output path end-to-end (Pi → YG300 board) before adding any complexity. Keep all sizes/positions in a separate `config.py` from the start.

### Task 3 — Full arrow set
Extend the renderer to support all 7 `TurnDirection` shapes (`forward`, `left`, `right`, `keepLeft`, `keepRight`, `uTurn`, `roundabout`), matching the shapes of the parent app's `DynamicArrowWidget` (chevrons for forward/left/right, smaller angled chevrons for keep-left/right, U-shaped arc for uTurn, 3/4-circle arc with exit number for roundabout). Add a simple way to cycle through them manually for testing (e.g. keyboard input) — a dev aid, to be removed or gated later.

### Task 4 — Distance text and approach-stage colour
Add distance text display and colour switching by `stage` (far/green, approaching/amber, imminent/red), per REQUIREMENTS.md FR-07/FR-08.

### Task 5 — Listener module
**Status: done on the PC; not yet verified on the Pi.** Implemented as a UDP listener on port 5005 (`src/listener.py`), with `src/send_test.py` to simulate the phone.

Write `listener.py`: a UDP listener on port 5005 that receives one JSON packet per message, parses it against the data contract in REQUIREMENTS.md, ignores malformed packets, and exposes the latest valid state for the renderer to read. UDP is connectionless, so there is nothing to reconnect. Write `send_test.py` to simulate the phone sending test packets, so this can be verified without the Flutter app.

### Task 6 — Wire listener and renderer together
**Status: done on the PC; not yet verified on the Pi.** `src/main.py` runs live mode by default (black screen until data arrives or after 5 s without data), `--demo` for the keyboard dev mode, and `--windowed`.

Write `main.py` to start both modules together. The renderer should read live state from the listener instead of hardcoded test values, and the screen should be plain black (FR-12) until data arrives or after 5 seconds without data.

### Task 7 — Config centralization pass
Review all files and confirm no tunable value (size, offset, colour, margin) is hardcoded outside `config.py`, per FR-11/NFR-03. Physical lens and combiner testing will need fast iteration on these values.

### Task 8 — Documentation pass
Update HARDWARE.md's "Setup steps remaining" checklist to reflect what's been completed, and note any deviations from the plan discovered during implementation.

---

## Not yet scoped (do not start without explicit instruction)
- The phone-side `HudBroadcastService` (lives in the parent Flutter repo, not here).
- Auto-start/systemd service for headless operation in the vehicle.
- Keystone pre-warp correction (only needed if physical testing shows visible skew).
- A 2D map view on the phone while connected to the Pi (new idea, needs its own design pass).

## Possible future work
Animations from the parent app's `DynamicArrowWidget` that were left out of the HUD renderer for now (the stepped flow wave was kept):
- **Pulse:** scale 0.9 ↔ 1.1, faster as the turn gets closer (2000 / 1000 / 400 ms for far / approaching / imminent).
- **Direction-change pop:** scale 1.0 → 1.3 → 1.0 over 300 ms (ease-out, then elastic) when the direction changes.
- **Colour cross-fade:** 400 ms ease-in-out blend between approach-stage colours.

Scaling animations would mean re-rasterising (or caching several sizes of) the supersampled arrow, so check the cost on the Pi first.

---

*Prepared by: Liew Sau Yang | Sunway University | Bachelor of Software Engineering (Hons)*
