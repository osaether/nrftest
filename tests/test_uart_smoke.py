"""Host checker tests; no board or pyserial installation required."""

import unittest

from scripts.uart_smoke import check_bytes


class FakePort:
    def __init__(self, mode="normal"):
        self.mode = mode
        self.pending = bytearray()

    def write(self, data):
        if self.mode == "short":
            return 0
        if self.mode != "timeout":
            self.pending.extend(data if self.mode == "loopback"
                                else bytes(value ^ 0xA5 for value in data))
        return len(data)

    def read(self, size):
        result = bytes(self.pending[:size])
        del self.pending[:size]
        return result


class CheckerTests(unittest.TestCase):
    def test_all_byte_values(self):
        check_bytes(FakePort(), bytes(range(256)))

    def test_rejects_timeout_loopback_and_short_write(self):
        for mode in ("timeout", "loopback", "short"):
            with self.subTest(mode=mode), self.assertRaises(RuntimeError):
                check_bytes(FakePort(mode), b"\x00\xff")

    def test_rejects_unsolicited_output(self):
        port = FakePort()
        port.pending.extend(b"\xa5\xff")
        with self.assertRaisesRegex(RuntimeError, "trailing"):
            check_bytes(port, b"\x00")


if __name__ == "__main__":
    unittest.main()
