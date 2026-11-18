# Architecture

## Smart AR HUD — Raspberry Pi Extension

---

## 1. System Diagram

```
Phone (parent repo, Flutter)
   │  ARViewModel.updateAROverlay() fires on each GPS tick
   │  HudBroadcastService serializes state to JSON
   │  sent as one JSON packet per message, over either or both:
   │    • Wi-Fi UDP broadcast, port 5005
   │    • Bluetooth LE GATT write to "ARoute-HUD"
   ▼
Raspberry Pi (this repo)
   │  listener.py     — UDP: receives JSON  ┐ both validate via the same
   │  ble_listener.py — BLE: receives JSON  ┘ parse_packet() into one LatestState
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
- **Primary transport: UDP broadcast over the local Wi-Fi, port 5005**, chosen for low overhead on continuous per-second updates and no meaningful payload-size constraint. Each message is one JSON packet. UDP is connectionless: there is no connection to set up or lose, so nothing has to reconnect when the phone drops off or comes back.
- **Second transport: Bluetooth LE.** The Pi is a GATT peripheral advertising as `ARoute-HUD` with service `7d6a0001-3b1e-4f5c-9a52-0a1c5e8b4d10` and one characteristic `7d6a0002-3b1e-4f5c-9a52-0a1c5e8b4d10` (write and write-without-response). Each write is one UTF-8 JSON packet in exactly the UDP format. This works without the phone hotspot. The phone is the BLE central, so it is responsible for reconnecting; the Pi keeps advertising and accepts whichever connection comes next. Payload size depends on the negotiated MTU (see HARDWARE.md section 6).
- **Transport selection:** `main.py --transport udp|ble|both` (default `both`). Both transports feed one shared latest-state store, so the HUD shows whichever valid packet arrived last, whatever its source.
- **One-directional:** phone → Pi only. The Pi does not need to send anything back for the current scope.

## 3. Modules (this repo)

### 3.1 `listener.py`
- Binds a UDP socket on port 5005 and receives one JSON packet per message (no connection to accept).
- Parses incoming JSON against the data contract in REQUIREMENTS.md.
- Stores the latest valid state, with the time it arrived, in a small thread-safe shared object (`LatestState`) that the render loop reads from. Malformed packets are ignored.
- `parse_packet()` and `LatestState` are the single validation and storage path, which the BLE listener reuses.
- Needs no reconnection handling — when the phone stops sending (navigation ends, Wi-Fi drops), packets simply stop arriving; when it starts again, the next valid packet is used.
- Runs on its own background thread, independent of the render loop, so a slow or silent network never blocks drawing.

### 3.1a `ble_listener.py`
- Runs a `bless` GATT server (BlueZ over D-Bus) on its own asyncio event loop in a daemon thread, so it never blocks the render loop.
- Advertises `ARoute-HUD` with the service and characteristic UUIDs above; each write's bytes go to `LatestState.submit()`, the same validation and timestamping the UDP path uses.
- `start()` waits for the service to register and advertising to begin, and raises if BlueZ is unavailable. `bless` is imported only when BLE is requested, so `--transport udp` runs on machines without it.

### 3.2 `renderer.py`
- Opens a full-screen Pygame window sized to the Pi's HDMI output.
- On each frame, reads the latest state from the listener and draws:
  - The arrow shape matching `direction` (same 7 shapes conceptually as the parent app's `DynamicArrowWidget` — chevrons, keep-left/right variants, U-arc, roundabout arc).
  - The `distance` value as text (or the roundabout `exit` number).
  - Colour selected by `stage`.
- Draws against pure black background, content kept within a configurable safe margin from the edges.
- Idle screen: when no valid packet has arrived yet, or none for 5 seconds, `main.py` shows a plain black screen instead (nothing is projected).

### 3.3 `config.py`
- Holds all tunable constants: arrow size, position offsets, font size/family, colour values per approach stage, safe-margin size, window/display resolution.
- Nothing in `renderer.py` should hardcode a number that belongs here.

### 3.4 `main.py`
- Entry point. Starts the listener(s) and the renderer together, and blanks the screen after 5 seconds without data from any transport.
- `--transport udp|ble|both` (default `both`). With `both`, a transport that fails to start (no adapter, `bless` not installed) is reported as a warning and the HUD runs on the other; with a single transport, a startup failure is an error.
- `--demo` runs the keyboard dev mode (no phone needed); `--windowed` opens a window instead of fullscreen.

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
