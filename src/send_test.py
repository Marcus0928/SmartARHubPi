"""Simulate the phone: send test packets to the HUD listener over UDP.

    python send_test.py                      # to this machine
    python send_test.py --host 192.168.x.y   # to the Pi

Cycles through every direction and stage once per --interval seconds, and
sends one malformed packet per cycle (the HUD should ignore it). Stop it with
Ctrl+C; the HUD should go blank STALE_TIMEOUT_S seconds later.
"""

import argparse
import itertools
import json
import socket
import time

import config

DIRECTIONS = ("forward", "left", "right", "keepLeft", "keepRight", "uTurn", "roundabout")
STAGES = (("far", 500), ("approaching", 120), ("imminent", 30))


def main():
    parser = argparse.ArgumentParser(description="Send test HUD packets")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=config.LISTEN_PORT)
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between packets")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (args.host, args.port)
    print(f"sending to {args.host}:{args.port} (Ctrl+C to stop)")
    # 7 directions x 3 stages are coprime, so every combination comes up every 21 packets.
    for direction, (stage, distance) in zip(itertools.cycle(DIRECTIONS), itertools.cycle(STAGES)):
        msg = {
            "direction": direction,
            "distance": distance,
            "street": "Jalan Universiti",
            "stage": stage,
            "exit": 2 if direction == "roundabout" else None,
        }
        sock.sendto(json.dumps(msg).encode("utf-8"), target)
        print("sent", msg)
        if direction == "roundabout":
            sock.sendto(b'{"direction": "sideways", "distance": -1}', target)
            print("sent malformed packet")
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
