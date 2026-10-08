#!/usr/bin/env python3
"""Exercise the DK UART using a binary, stop-and-wait challenge/response."""

import argparse
import math
import random
import sys
import time


def check_bytes(port, payload):
    """Raise on timeout, short write, corruption, or extra response bytes."""
    for index, value in enumerate(payload):
        if port.write(bytes([value])) != 1:
            raise RuntimeError(f"short write at byte {index}")
        actual = port.read(1)
        expected = bytes([value ^ 0xA5])
        if actual != expected:
            received = actual.hex() if actual else "timeout"
            raise RuntimeError(
                f"byte {index}: sent {value:02x}, expected {expected.hex()}, "
                f"received {received}"
            )
    extra = port.read(1)
    if extra:
        raise RuntimeError(f"unexpected trailing byte: {extra.hex()}")


def positive_int(value):
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def positive_float(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", help="e.g. /dev/ttyACM0, /dev/cu.usbmodem..., or COM5")
    parser.add_argument("--rounds", type=positive_int, default=3)
    parser.add_argument("--timeout", type=positive_float, default=1.0,
                        help="per-byte read/write timeout in seconds (default: 1)")
    args = parser.parse_args()
    try:
        import serial
    except ImportError:
        print("FAIL: install dependencies: python -m pip install -r requirements.txt",
              file=sys.stderr)
        return 1

    # Cover every byte, including NUL, CR/LF, XON/XOFF, and high-bit data,
    # then repeat them in a different order to expose stale/shifted responses.
    shuffled = list(range(256))
    random.Random(52840).shuffle(shuffled)
    payload = bytes(range(256)) + bytes(shuffled)
    try:
        with serial.Serial(args.port, baudrate=115200, bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                           timeout=args.timeout, write_timeout=args.timeout,
                           xonxoff=False, rtscts=False, dsrdtr=False) as port:
            time.sleep(2.0)  # Allow the board/debugger to settle after port open.
            port.reset_input_buffer()
            for round_number in range(1, args.rounds + 1):
                check_bytes(port, payload)
                print(f"Round {round_number}/{args.rounds}: {len(payload)} bytes OK")
    except (serial.SerialException, OSError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {args.rounds * len(payload)} bytes verified at 115200 baud, 8N1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
