"""Bluetooth LE listener: a GATT peripheral the phone writes JSON packets to.

The Pi advertises as "ARoute-HUD" (config.BLE_DEVICE_NAME) with one service
and one writable characteristic (write and write-without-response). Each
write holds one UTF-8 JSON packet in exactly the UDP format:

    {"direction": "left", "distance": 320, "street": "Jalan Universiti",
     "stage": "approaching", "exit": null}

Packets go through listener.LatestState, the same validation and
latest-state storage the UDP listener uses. Malformed writes are dropped
silently, the same as malformed UDP packets.

Uses the `bless` library, which talks to BlueZ over D-Bus on Raspberry Pi OS.
bless runs on asyncio, so the server gets its own event loop on a daemon
thread and the render loop is never blocked.

Packet size: a write-without-response must fit in one ATT packet (MTU - 3
bytes). The default MTU of 23 leaves only 20 bytes, so the phone must
negotiate a larger MTU first (e.g. 185). Write-with-response also works at the
default MTU, because BlueZ reassembles long writes before passing them on.
"""

import asyncio
import threading

from bless import (
    BlessServer,
    GATTAttributePermissions,
    GATTCharacteristicProperties,
)

import config
from listener import LatestState


class BleListener:
    """Runs a BLE GATT server on a daemon thread; latest() is safe to call from any thread."""

    def __init__(self, name=config.BLE_DEVICE_NAME, store=None):
        self._name = name
        self._store = store if store is not None else LatestState()
        self._ready = threading.Event()
        self._error = None
        self._loop = None
        self._stop_event = None
        self._thread = None

    def start(self):
        """Start advertising. Raises if BlueZ is unavailable or the service can't be registered."""
        self._thread = threading.Thread(target=self._run, name="ble-listener", daemon=True)
        self._thread.start()
        if not self._ready.wait(config.BLE_START_TIMEOUT_S):
            self.stop()
            raise TimeoutError(f"BLE server did not start within {config.BLE_START_TIMEOUT_S} s")
        if self._error is not None:
            raise RuntimeError(f"BLE server failed to start: {self._error!r}") from self._error
        return self

    def stop(self):
        loop, stop_event = self._loop, self._stop_event
        if loop is not None and stop_event is not None and not loop.is_closed():
            try:
                loop.call_soon_threadsafe(stop_event.set)
            except RuntimeError:
                pass  # loop already shut down
        if self._thread is not None:
            self._thread.join(timeout=config.BLE_START_TIMEOUT_S)

    def latest(self):
        """The most recent valid NavState, or None if nothing valid has arrived."""
        return self._store.latest()

    # --- server thread -------------------------------------------------------

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._serve())
        except Exception as exc:  # report startup failures to start()
            self._error = exc
        finally:
            self._ready.set()
            loop.close()

    async def _serve(self):
        self._stop_event = asyncio.Event()
        server = BlessServer(name=self._name, loop=asyncio.get_running_loop())
        server.read_request_func = self._on_read
        server.write_request_func = self._on_write

        await server.add_new_service(config.BLE_SERVICE_UUID)
        await server.add_new_characteristic(
            config.BLE_SERVICE_UUID,
            config.BLE_CHARACTERISTIC_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable,
        )
        await server.start()
        self._ready.set()
        try:
            await self._stop_event.wait()
        finally:
            await server.stop()

    def _on_write(self, characteristic, value, **kwargs):
        # Called on the server's event loop for every write, with or without response.
        self._store.submit(bytes(value))

    def _on_read(self, characteristic, **kwargs):
        # The characteristic isn't readable; bless still expects a read handler.
        return characteristic.value
