# nRF52840 DK UART smoke test

A small Zephyr application and Python host checker for the **nRF52840 DK
(PCA10056)**. It exercises UART0 RX and TX through the onboard debugger's
virtual COM port at **115200 baud, 8 data bits, no parity, 1 stop bit, no
flow control**. No jumper wires or external USB/UART adapter are needed.

The firmware replies to each received byte with `byte XOR 0xA5`. This checks
that the firmware actually processes the data: a simple TX/RX short will fail.
Console, logging and boot banners are disabled to keep the binary stream clean.

## Build and flash

Use an installed Zephyr or nRF Connect SDK development environment with its
matching toolchain. The application uses current Zephyr board naming
(`nrf52840dk/nrf52840`, as in Zephyr 4.2). This repository does not install or
pin an SDK; activate your SDK terminal first. For initial SDK setup see the
[Zephyr getting started guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)
or Nordic's nRF Connect for VS Code setup.

From the root of this repository, in the activated SDK environment:

```sh
west build -p always -b nrf52840dk/nrf52840 . -d build
west flash -d build
```

Flashing replaces the application currently on the DK. Connect the board's
**debugger USB connector** to the computer using a data-capable USB cable and
turn the board on. Do not use the nRF52840 native USB connector for this test.
The SDK's supported debugger/programming tools must also be installed for
`west flash` to work.

**LED1 on** means the UART is initialized and ready. **LED2 on** indicates
initialization failure or a latched UART error; reset the board before retrying.
An early GPIO initialization failure can leave both LEDs off. LED1 is a ready
indicator, not a test-pass indicator: only the host checker reports PASS.

## Run the smoke test

Install Python 3 and the host dependency (optionally in a virtual environment):

```sh
python -m pip install -r requirements.txt
python -m serial.tools.list_ports -v
python scripts/uart_smoke.py /dev/ttyACM0
```

Select the DK debugger's serial port from the listing. On Windows, for example:

```powershell
python scripts/uart_smoke.py COM5
```

On macOS use the matching `/dev/cu.usbmodem...` device. Close other serial
terminals before testing. On Linux your account needs permission to open the
serial device (commonly membership in the `dialout` group).

Expected final output with the default three rounds:

```text
Round 1/3: 512 bytes OK
Round 2/3: 512 bytes OK
Round 3/3: 512 bytes OK
PASS: 1536 bytes verified at 115200 baud, 8N1
```

Each round sends all 256 byte values in ascending order and then in a fixed
shuffled order. The host waits for each response before sending the next byte.
Timeouts, incorrect bytes, short writes, unexpected trailing data, and serial
port errors produce `FAIL` and exit status 1. Success exits with status 0;
invalid command-line arguments exit with status 2.

```sh
python scripts/uart_smoke.py /dev/ttyACM0 --rounds 10 --timeout 2
```

`--timeout` is a per-byte timeout in seconds. The checker allows two seconds
after opening the port for startup, then discards stale input before testing.
There is no text banner, shell or terminal echo: responses are binary.

## Wiring and scope

The standard board UART0 pin routing is TX **P0.06**, RX **P0.08**, connected
to the onboard debugger. The board's default pinctrl is retained; hardware
flow control is explicitly disabled in both firmware and host settings.
See the [Zephyr board documentation](https://docs.zephyrproject.org/latest/boards/nordic/nrf52840dk/doc/index.html)
and [UART API](https://docs.zephyrproject.org/latest/hardware/peripherals/uart.html).

This is a basic bidirectional UART smoke test, not a throughput, burst-load,
RTS/CTS, asynchronous-DMA, or low-power test. Stop-and-wait deliberately avoids
requiring an interrupt-driven receive buffer. Do not send continuous bursts
from another program. If a UART error is detected, the firmware stops replying
and lights LED2. No UART1 or radio functionality is exercised.

If the test times out, check LED1, the selected COM port, debugger USB cable,
board power, and whether the correct firmware was flashed. A PASS establishes
data integrity for this exchange, not the identity of the attached board.

## Development checks and validation status

Run the host checker tests without hardware or pyserial:

```sh
python -m unittest discover -s tests -v
```

These tests cover all byte values and rejection of timeouts, a plain loopback,
short writes and unsolicited output. They do not emulate the UART driver.
The initial implementation was checked with these host tests; firmware
compilation and an on-board run still require an SDK/toolchain and a physical DK.
