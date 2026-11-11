"""UDP listener for turn-by-turn state sent by the phone (Task 5).

The phone sends one JSON object per UDP datagram:

    {"direction": "left", "distance": 320, "street": "Jalan Universiti",
     "stage": "approaching", "exit": null}

A background thread receives packets, validates them, and keeps the most
recent valid one (with the time it arrived) for the render loop to read.
Malformed packets are dropped silently. UDP is connectionless, so the phone
dropping off and coming back needs no reconnect handling.

Test without the phone:  python send_test.py
"""

import json
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional

import config

DIRECTIONS = frozenset(("forward", "left", "right", "keepLeft", "keepRight", "uTurn", "roundabout"))
STAGES = frozenset(("far", "approaching", "imminent"))

_RECV_TIMEOUT_S = 0.5  # how often the thread checks whether it should stop


@dataclass(frozen=True)
class NavState:
    direction: str
    distance_m: float
    street: str
    stage: str
    exit_number: Optional[int]
    received_at: float  # time.monotonic() when the packet arrived


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parse_packet(data, received_at):
    """Return a NavState for a valid packet, or None if it is malformed."""
    try:
        msg = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(msg, dict):
        return None

    direction = msg.get("direction")
    distance = msg.get("distance")
    street = msg.get("street", "")
    stage = msg.get("stage")
    exit_number = msg.get("exit")

    if direction not in DIRECTIONS or stage not in STAGES:
        return None
    if not _is_number(distance) or not distance >= 0 or distance == float("inf"):
        return None
    if street is None:
        street = ""
    if not isinstance(street, str):
        return None
    if exit_number is not None and (not isinstance(exit_number, int) or isinstance(exit_number, bool)):
        return None

    return NavState(direction, float(distance), street, stage, exit_number, received_at)


class Listener:
    """Receives packets on a daemon thread; latest() is safe to call from any thread."""

    def __init__(self, host=config.LISTEN_HOST, port=config.LISTEN_PORT):
        self._addr = (host, port)
        self._lock = threading.Lock()
        self._latest = None
        self._stop = threading.Event()
        self._sock = None
        self._thread = None

    def start(self):
        # Bind here (not in the thread) so a port-in-use error surfaces to the caller.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self._addr)
        sock.settimeout(_RECV_TIMEOUT_S)
        self._sock = sock
        self._thread = threading.Thread(target=self._run, name="udp-listener", daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2 * _RECV_TIMEOUT_S)
        if self._sock is not None:
            self._sock.close()

    def latest(self):
        """The most recent valid NavState, or None if nothing valid has arrived."""
        with self._lock:
            return self._latest

    def _run(self):
        while not self._stop.is_set():
            try:
                data, _ = self._sock.recvfrom(config.LISTEN_MAX_PACKET_BYTES)
            except socket.timeout:
                continue
            except OSError:
                # e.g. Windows reports ICMP port-unreachable as a recv error on UDP
                # sockets, or the socket was closed by stop(). Keep going until stopped.
                continue
            state = parse_packet(data, time.monotonic())
            if state is not None:
                with self._lock:
                    self._latest = state
