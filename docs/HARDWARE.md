# Hardware Build Log

## Smart AR HUD — Raspberry Pi Extension

---

## 1. Parts confirmed

| Part | Status | Notes |
|---|---|---|
| Raspberry Pi 3 Model B+ | ✅ Working | Genuine board, confirmed boots to Raspberry Pi OS desktop. Full-size HDMI, micro-USB power (5V/2.5A adapter included), built-in Wi-Fi + Bluetooth (Bluetooth LE used as a second transport alongside UDP; see section 6). |
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
- **The BLE characteristic is unauthenticated**: any phone in range can connect and write packets, and the same is true of the UDP port on the hotspot network. Acceptable for a demo; add pairing/encryption before anything beyond that.

## 4. Setup steps completed

1. Confirmed genuine Pi 3B+ board and power adapter from the kit.
2. Confirmed the microSD card boots to a working Raspberry Pi OS desktop (pre-imaged by the kit seller; no reflash needed).
3. Confirmed Python 3 present on the Pi.
4. Removed YG300 outer case; identified driver board, LCD panel + lens assembly, HDMI port location, and power input type.
5. Confirmed Pi → HDMI → YG300 video path works (Pi desktop visible once the projector input was switched to HDMI).

## 5. Setup steps remaining

1. Confirm Pygame installed on the Pi (`python3 -c "import pygame; print(pygame.version.ver)"`); install if missing (`pip3 install pygame`).
2. Pre-configure the Pi's Wi-Fi with the phone's hotspot credentials while a monitor/keyboard is still attached.
3. Install `bless` and configure BlueZ for the BLE transport (section 6), then test it with nRF Connect (section 7).
4. Build and test the close-focus lens stack at the real target distance.
5. Choose and test combiner material/tint level.
6. Build a temporary housing (cardboard/foam-core acceptable) to hold LCD + lens + driver board in a fixed position.
7. Only then: a permanent housing and in-vehicle mount.

## 6. Bluetooth LE setup (Pi)

`src/ble_listener.py` makes the Pi a BLE GATT peripheral using the `bless` library, which talks to BlueZ (the Linux Bluetooth stack) over D-Bus. Nothing needs compiling: on Linux `bless` only pulls in the pure-Python `dbus-next`.

| Item | Value |
|---|---|
| Advertised name | `ARoute-HUD` |
| Service UUID | `7d6a0001-3b1e-4f5c-9a52-0a1c5e8b4d10` |
| Characteristic UUID | `7d6a0002-3b1e-4f5c-9a52-0a1c5e8b4d10`, write + write-without-response |
| Payload | One UTF-8 JSON packet per write, same format as UDP (REQUIREMENTS.md FR-14) |

**Install** (Raspberry Pi OS Bookworm blocks system-wide `pip install`, so use a venv; `--system-site-packages` keeps an apt-installed Pygame visible):

```bash
sudo apt update
sudo apt install -y bluez python3-venv
python3 -m venv --system-site-packages ~/hud-venv
~/hud-venv/bin/pip install -r src/requirements.txt
cd src && ~/hud-venv/bin/python main.py --transport both
```

**BlueZ settings:**

1. **Bluetooth service running and adapter unblocked and powered:**
   ```bash
   sudo systemctl enable --now bluetooth
   sudo rfkill unblock bluetooth
   bluetoothctl power on
   bluetoothctl show        # expect "Powered: yes"
   ```
2. **Power on at boot:** in `/etc/bluetooth/main.conf`, under `[Policy]`, set `AutoEnable=true`, then `sudo systemctl restart bluetooth`.
3. **BlueZ version 5.50 or newer** (`bluetoothctl --version`; Bookworm ships 5.66). The GATT server and LE advertising D-Bus APIs are stable there, so `bluetoothd` does **not** need `--experimental`. On an older image, if bless reports that `LEAdvertisingManager1` is missing, run `sudo systemctl edit bluetooth`, override `ExecStart=` with the path from `systemctl cat bluetooth` plus `--experimental`, then restart the service.
4. **D-Bus permission:** the user running the HUD must be in the `bluetooth` group (the default `pi` user already is). Check with `groups`; if missing, run `sudo usermod -aG bluetooth $USER` and log in again. No need to run the HUD as root.
5. **Device name (optional but recommended):** the advert's 31 bytes are mostly taken up by the flags and the 128-bit service UUID, so some phones show the Pi's hostname instead of `ARoute-HUD`, or show it only after connecting. Run `bluetoothctl system-alias ARoute-HUD` so the adapter's own name matches.
6. **No pairing:** the characteristic is open (no encryption or bonding), so phones connect without a PIN. This is acceptable for a demo but means anyone in range could write packets. See section 3.

**Packet size:** a write-without-response must fit in one ATT packet (MTU minus 3 bytes). At the default MTU of 23 that leaves 20 bytes, smaller than a typical ~100-byte packet. The phone must negotiate a larger MTU first (iOS does this automatically; on Android call `requestMtu(185)` or higher). Write-with-response works at any MTU, because BlueZ reassembles long writes.

**Pi 3B+ note:** Wi-Fi and Bluetooth share one radio chip. Running both transports works, but heavy Wi-Fi traffic can add BLE latency.

## 7. Testing with nRF Connect

Tests the BLE path from a phone without the Flutter app, using the free nRF Connect for Mobile app (Android/iOS).

1. On the Pi: `cd src && ~/hud-venv/bin/python main.py --transport ble --windowed`. It should print `advertising BLE as 'ARoute-HUD'`. The screen stays black.
2. In nRF Connect, go to **Scanner**, find **ARoute-HUD** (or the Pi's hostname, see setting 5 above), and tap **Connect**.
3. **Android only:** open the ⋮ menu, choose **Request MTU**, and enter `247`. Without this, write-without-response packets are cut to 20 bytes and dropped as invalid JSON.
4. Expand the service `7d6a0001-…`. The characteristic `7d6a0002-…` should list the properties **WRITE** and **WRITE NO RESPONSE**. Tap its upload (↑) icon.
5. Set the value type to **Text (UTF-8)** and send:
   ```json
   {"direction":"left","distance":320,"street":"Jalan Universiti","stage":"approaching","exit":null}
   ```
   The HUD should show the left arrow in amber with "320 m". Try a roundabout too: `{"direction":"roundabout","distance":30,"stage":"imminent","exit":2}`.
6. Send both write types, request (with response) and command (without response), if the dialog offers the choice.
7. Send malformed text (e.g. `hello`): the HUD should ignore it and keep the last arrow.
8. Stop writing: the screen should go black 5 seconds after the last valid packet.

If nRF Connect shows old or missing services after the Pi's GATT layout changes, use **Refresh services** from the ⋮ menu, or turn the phone's Bluetooth off and on to clear Android's GATT cache.

---

*Prepared by: Liew Sau Yang | Sunway University | Bachelor of Software Engineering (Hons)*
