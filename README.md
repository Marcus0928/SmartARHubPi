# Smart AR HUD — Raspberry Pi Extension

## Companion project to Smart AR Navigation App (Sunway University FYP)

---

| Field | Details |
|---|---|
| **Project Title** | Smart AR HUD — Raspberry Pi Extension |
| **Parent Project** | Smart AR Navigation App for Enhanced Driving Assistance |
| **Author** | Liew Sau Yang (22062475) |
| **Institution** | Sunway University — School of Computing and Artificial Intelligence |
| **Language** | Python 3 (Pygame) |
| **Status** | Experimental — not part of the graded FYP (CP2) deliverable |

---

## About

This project extends the Smart AR Navigation App with a physical heads-up display. While the phone runs active navigation as normal, it streams live turn-by-turn data over Wi-Fi to a Raspberry Pi. The Pi renders a minimal arrow-and-distance display and outputs it via HDMI to a modified YG300 pico projector, which projects onto a small combiner mounted on the vehicle dashboard — giving the driver an AR-style cue reflected into their line of sight, separate from the phone's own screen.

This repo contains only the **Raspberry Pi side** — the network listener and the renderer. The Flutter app lives in a separate repo and is not touched by this project beyond one small addition described in `REQUIREMENTS.md`.

## Documentation

| Document | Description |
|---|---|
| [REQUIREMENTS.md](REQUIREMENTS.md) | What the system must do — functional requirements |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How it's built — data flow, modules, networking design |
| [HARDWARE.md](HARDWARE.md) | Physical build log — parts, teardown notes, known constraints |
| [TASKS.md](TASKS.md) | Implementation task list |

## Project structure

```
SmartARHubPi/
├── README.md
├── docs/
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── HARDWARE.md
│   └── TASKS.md
└── src/
    ├── requirements.txt     # pygame
    ├── main.py              # entry point — starts listener + renderer
    ├── listener.py          # receives JSON from the phone over Wi-Fi
    ├── renderer.py          # draws arrow + distance via Pygame
    ├── send_test.py         # simulates the phone: sends test UDP packets
    └── config.py            # all tunable constants (sizes, offsets, colours)
```

## Quick status

- Raspberry Pi 3B+ confirmed booting to Raspberry Pi OS desktop.
- YG300 projector case removed; HDMI confirmed on main driver board; powers via USB-C.
- Renderer done: all 7 arrow shapes, distance label and approach-stage colours, with a `--demo` keyboard mode for previewing shapes.
- Listener done: receives UDP JSON from the phone on port 5005; the screen goes black after 5 seconds without data.
- `send_test.py` done: simulates the phone by sending test packets.
- The above has been run on a PC only. **Next step:** test live data on the Pi through the projector.
- No close-focus lens or combiner testing done yet.
- No housing built yet.

## Relationship to the parent app

This project only *consumes* data the parent app already computes. It does not fork or duplicate any navigation, routing, or turn-tracking logic, and nothing here is part of the graded CP2 submission.

---

*Prepared by: Liew Sau Yang | Sunway University | Bachelor of Software Engineering (Hons)*
