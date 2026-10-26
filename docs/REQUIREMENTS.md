# Requirements

## Smart AR HUD — Raspberry Pi Extension

---

## 1. Purpose

Defines what the Pi-side software must do to receive navigation state from the phone and render it as a projected AR cue.

## 2. Scope

Covers only the Raspberry Pi-side listener and renderer. Does not cover the phone app beyond the one small addition noted in FR-01.

## 3. Functional Requirements

### 3.1 Phone-side integration (parent repo, not this repo)

| ID | Requirement |
|---|---|
| FR-01 | The parent Flutter app shall gain a small `HudBroadcastService` that reads `ARViewModel` state on every `updateAROverlay()` call and sends it as JSON to the Pi over a Wi-Fi socket. This must not alter or depend on any existing navigation logic, and must fail silently (no crash, no blocking) if the Pi is unreachable. |

### 3.2 Networking (this repo)

| ID | Requirement |
|---|---|
| FR-02 | The Pi shall connect to a pre-configured Wi-Fi hotspot hosted by the phone, using saved credentials configured before the Pi is deployed in the vehicle (no screen/keyboard available once mounted). |
| FR-03 | The Pi shall run a listener that accepts incoming JSON messages over a local Wi-Fi socket/WebSocket connection. |
| FR-04 | The listener shall tolerate connection loss and reconnect automatically without crashing or requiring a manual restart. |
| FR-05 | The listener shall hold the most recently received state in memory for the renderer to read; it must not block rendering while waiting for a new message. |

### 3.3 Rendering

| ID | Requirement |
|---|---|
| FR-06 | The renderer shall draw a directional arrow matching one of the 7 `TurnDirection` values used in the parent app: `forward`, `left`, `right`, `keepLeft`, `keepRight`, `uTurn`, `roundabout`. |
| FR-07 | The renderer shall display the distance to the next turn as text, using the same value received in the JSON payload. |
| FR-08 | The renderer shall colour the arrow according to `approachStage`: far/green, approaching/amber, imminent/red — matching the parent app's existing colour tiers. |
| FR-09 | The renderer shall use a pure black background with no camera feed or UI chrome — only the arrow and distance text. |
| FR-10 | The renderer shall keep all visible content centred within a configurable safe area, away from frame edges, to tolerate the vignetting/softness expected from the close-focus lens hack (see HARDWARE.md). |
| FR-11 | Arrow size, position offsets, font size, and colours shall be defined as named constants in one config location, not hardcoded inline, to support rapid iteration during physical testing. |
| FR-12 | If no data has been received yet (fresh start, or Pi not yet connected to the phone), the renderer shall show an idle/placeholder state rather than crashing or showing a blank/undefined screen. |
| FR-13 | The renderer shall output to the Pi's HDMI port at a resolution and refresh rate compatible with the YG300 driver board's native input. |

### 3.4 Data contract

| ID | Requirement |
|---|---|
| FR-14 | The JSON payload exchanged between phone and Pi shall use the following shape: |

```json
{
  "direction": "left",
  "distanceToNextTurn": 320,
  "streetName": "Jalan Universiti",
  "approachStage": "approaching"
}
```

| Field | Type | Allowed values |
|---|---|---|
| `direction` | string | `forward`, `left`, `right`, `keepLeft`, `keepRight`, `uTurn`, `roundabout` |
| `distanceToNextTurn` | number (metres) | any non-negative number |
| `streetName` | string | any (may be empty) |
| `approachStage` | string | `far`, `approaching`, `imminent` |

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | The renderer shall update visibly within roughly 1 second of receiving new data, matching the parent app's GPS update cadence. |
| NFR-02 | The system shall not require any display, keyboard, or mouse once deployed — all interaction happens via the Wi-Fi link from the phone. |
| NFR-03 | The codebase shall be simple enough to tune (sizes, offsets, colours) without needing to touch core logic — see FR-11. |
| NFR-04 | The system is experimental and does not need production-grade error handling beyond not crashing (FR-04, FR-12). |

## 5. Out of Scope

- Any change to the parent app's core navigation, routing, or turn-tracking logic.
- Voice guidance, traffic delay notification, or any other parent-app feature — this project only consumes the arrow/distance/street-name/approach-stage subset of state.
- Production packaging, auto-start on boot, or installer scripts (may be added later, not required for initial build).

## 6. Future idea (not a committed requirement)

The parent app originally planned a 2D map view but cut it for time, falling back to AR-camera-only navigation. With the HUD showing the arrow externally, the phone could show a 2D map while connected to the Pi. This needs its own design pass in the parent repo before it becomes a requirement.

---

*Prepared by: Liew Sau Yang | Sunway University | Bachelor of Software Engineering (Hons)*
