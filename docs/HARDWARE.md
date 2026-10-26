# Hardware Build Log

## Smart AR HUD — Raspberry Pi Extension

---

## 1. Parts confirmed

| Part | Status | Notes |
|---|---|---|
| Raspberry Pi 3 Model B+ | ✅ Working | Genuine board, confirmed boots to Raspberry Pi OS desktop. Full-size HDMI, micro-USB power (5V/2.5A adapter included), built-in Wi-Fi + Bluetooth (Bluetooth unused in this design). |
| YG300 mini projector | ⚠️ Case removed, not yet tested at close range | Driver board has a full-size HDMI port soldered directly onto the main PCB — not a separate daughterboard on a fragile ribbon, safe to reposition. Power input is **USB-C**, not micro-USB as the general spec sheet suggests. LCD panel + lens assembly separated from the driver board during teardown, connected via a ribbon/flex cable. |
| Close-focus lens | ❌ Not started | Stock YG300 lens focuses at 0.8–2m. Target distance in the vehicle is ~20cm, well below native range. Plan: test stacking supplementary positive lenses (cheap assorted reading glasses, roughly +1 to +6 diopters) in front of the stock lens. Expect reduced image size, vignetting/softness at edges, some brightness loss. |
| Combiner | ❌ Not started | Plan: small tinted acrylic sheet or one-way reflective film. Test for best brightness vs see-through balance. |
| Housing/mount | ❌ Not started | The stock YG300 case did real structural work (LCD-to-lens alignment, ribbon strain relief, dust protection) and needs replacing. Options: reuse internal ribs from the original shell with the outer plastic cut away, or a cardboard/foam-core scaffold for early testing. |

## 2. Cabling

- Pi → YG300 driver board: standard HDMI-to-HDMI cable (both ends are full-size HDMI).
- Pi power: original 5V/2.5A micro-USB adapter.
- YG300 power: USB-C 5V source.
- During development the YG300 must be switched to its HDMI input source, otherwise it shows nothing.

## 3. Known constraints

- **Image will likely be small and centred** once the close-focus lens is in use — the stock throw-ratio table no longer applies. Design the renderer's safe-content area around this, not a full-frame layout.
- **Keystone distortion is expected** unless the projector can be mounted close to perpendicular to the combiner. If skew is visible, consider pre-warping the rendered shape in software rather than relying on the YG300's own correction menu, whose behaviour with external HDMI input is untested.
- **Brightness is the biggest risk.** The YG300 is dim in real use; expect demo footage in low light, and a tinted combiner to help.
- **No regulatory certification** on this unit's internals once modified — personal experimental/demo use only.

## 4. Setup steps completed

1. Confirmed genuine Pi 3B+ board and power adapter from the kit.
2. Confirmed the microSD card boots to a working Raspberry Pi OS desktop (pre-imaged by the kit seller; no reflash needed).
3. Confirmed Python 3 present on the Pi.
4. Removed YG300 outer case; identified driver board, LCD panel + lens assembly, HDMI port location, and power input type.
5. Confirmed Pi → HDMI → YG300 video path works (Pi desktop visible once the projector input was switched to HDMI).

## 5. Setup steps remaining

1. Confirm Pygame installed on the Pi (`python3 -m pygame --version`); install if missing (`pip3 install pygame`).
2. Pre-configure the Pi's Wi-Fi with the phone's hotspot credentials while a monitor/keyboard is still attached.
3. Build and test the close-focus lens stack at the real target distance.
4. Choose and test combiner material/tint level.
5. Build a temporary housing (cardboard/foam-core acceptable) to hold LCD + lens + driver board in a fixed position.
6. Only then: a permanent housing and in-vehicle mount.

---

*Prepared by: Liew Sau Yang | Sunway University | Bachelor of Software Engineering (Hons)*
