# VENATOR Ground Control Station Firmware

**Project:** VENATOR Senior Design  
**Subsystem:** Ground Control Station (GCS) Gateway  
**Platform:** Raspberry Pi Pico / RP2040  
**Language:** MicroPython  
**Primary developer:** David Ritter

## Overview

The VENATOR Ground Control Station firmware runs on a Raspberry Pi Pico and provides a local operator interface for selecting drone commands and sending them to a drone over a RYLR998 LoRa radio module.

The firmware uses a rotary encoder to navigate a three-command menu, an OLED display to show the menu and status messages, and pushbuttons for command selection and resetting the menu selection. The Pico communicates with the OLED over I²C and with the RYLR998 over UART using the radio's AT-command interface.

### Current capabilities

- Displays a three-item command menu on a 128 × 64 SSD1309 OLED.
- Uses a rotary encoder to select a menu item.
- Uses the encoder pushbutton to select and send a command.
- Uses a separate reset button to return the selection to the first menu item.
- Configures the RYLR998 radio using AT commands.
- Sends selected commands to LoRa address `2`.
- Prints radio responses and command activity to the MicroPython console.
- Displays placeholder coordinate values (`X:10`, `Y:20`, `Z:30`) on the OLED.

> **Development note:** The coordinate values shown on the display are placeholders. The code documented here does not yet implement receiving, parsing, or displaying live drone coordinates.

## Repository Structure

```text
.
├── main.py              # Main GCS firmware and operator interface
├── rotary.py            # Platform-independent rotary encoder library
├── rotary_irq_rp2.py    # Raspberry Pi Pico rotary encoder interrupt implementation
├── ssd1309.py           # SSD1309 I²C OLED driver
└── README.md            # Project documentation
```

Save the three library files on the Pico alongside `main.py` so the imports work.

## Hardware

- Raspberry Pi Pico (RP2040)
- RYLR998 LoRa module
- 2.42-inch, 128 × 64 SSD1309 I²C OLED display
- Rotary encoder with pushbutton
- Separate reset pushbutton
- Appropriate wiring and power connections for each module

## Wiring and Pin Configuration

| Raspberry Pi Pico pin | Connected hardware | Purpose |
|---|---|---|
| GPIO 0 | RYLR998 RX | UART transmit from Pico to radio |
| GPIO 1 | RYLR998 TX | UART receive from radio to Pico |
| GPIO 4 | OLED SDA | I²C data |
| GPIO 5 | OLED SCL | I²C clock |
| GPIO 6 | Rotary encoder CLK | Encoder channel A / clock input |
| GPIO 7 | Rotary encoder DT | Encoder channel B / data input |
| GPIO 8 | Encoder pushbutton | Select the highlighted command |
| GPIO 9 | Reset pushbutton | Reset selection to the first menu item |

### Communication settings

| Setting | Value |
|---|---|
| UART peripheral | UART 0 |
| UART baud rate | 115200 |
| OLED I²C interface | `SoftI2C` |
| OLED I²C frequency | 100 kHz |
| OLED I²C address | `0x3C` (driver default) |
| LoRa module | RYLR998 |
| Gateway LoRa address | `1` |
| Destination LoRa address | `2` |
| LoRa network ID | `5` |
| LoRa frequency | `915000000` Hz (915 MHz) |
| Radio parameters | `AT+PARAMETER=7,7,1,12` |

Verify the wiring and radio settings against the hardware before operation. The receiving radio must be configured with a compatible address, network ID, frequency, and radio parameters.

## Software Setup

1. Install a MicroPython firmware build compatible with the Raspberry Pi Pico.
2. Connect the Pico to your computer and open a MicroPython-compatible editor or serial terminal.
3. Copy `main.py`, `rotary.py`, `rotary_irq_rp2.py`, and `ssd1309.py` to the Pico's filesystem.
4. Wire the OLED, rotary encoder, buttons, and RYLR998 according to the pin table.
5. Confirm the radio power and UART wiring.
6. Run `main.py`. If saved as `main.py` on the device, MicroPython normally runs it on boot.

The code imports standard MicroPython modules (`machine`, `utime`, `framebuf`, and `micropython`) along with the three project/library files listed above.

## Operator Interface

| Selection index | Menu item | Message sent |
|---:|---|---|
| `0` | Takeoff | `Takeoff` |
| `1` | Get Coords | `Get Coords` |
| `2` | Go Home | `Go Home` |

- **Rotate the encoder:** Move through the menu. The selection is bounded from `0` to `2`.
- **Press the encoder button:** Display the selected command, send it over LoRa, and return the selection to the first item.
- **Press the reset button:** Reset the selection to `0`.

Button handling uses polling and delays in the main loop, so the firmware pauses briefly while handling a press.

## Main Firmware: `main.py`

### Initialization

At startup, `main.py` creates the software I²C interface, initializes the SSD1309 driver, configures UART 0 at 115200 baud, initializes the rotary encoder and buttons, sends radio configuration commands, and draws the initial menu.

### Functions

#### `display_menu(selected)`

Redraws the OLED command menu and highlights the selected item. It clears the framebuffer, draws the heading and three commands, draws the selection arrow, displays placeholder coordinate values, and refreshes the display using `oled.show()`.

#### `display_status(message)`

Draws a status message in the OLED status area and refreshes the display.

#### `send_command(command)`

Writes an AT command to the RYLR998 over UART. It encodes a Python string as ASCII bytes when needed, appends carriage return and line feed (`\r\n`), writes the command, waits 0.5 seconds, and prints any available response.

#### `initialize_lora()`

Sends the following configuration commands in sequence:

| AT command | Purpose |
|---|---|
| `AT` | Test communication with the module |
| `AT+ADDRESS=1` | Set the gateway radio address |
| `AT+NETWORKID=5` | Set the LoRa network ID |
| `AT+BAND=915000000` | Set the operating frequency to 915 MHz |
| `AT+PARAMETER=7,7,1,12` | Configure radio parameters |

The current implementation prints responses when available but does not explicitly validate that each command succeeded.

#### `send_message(task)`

Maps the selected menu index to a text command, formats an addressed RYLR998 send command, and passes it to `send_command()`.

The AT command format is:

```text
AT+SEND=<destination address>,<message length>,<message>
```

The current destination address is `2`, and the message length is calculated from the selected message string.

## Key Variables

| Variable | Description |
|---|---|
| `i2c` | Software I²C interface used by the OLED |
| `oled_width` | OLED width in pixels (`128`) |
| `oled_height` | OLED height in pixels (`64`) |
| `oled` | `SSD1309_I2C` display driver instance |
| `tasks` | List of commands: `Takeoff`, `Get Coords`, and `Go Home` |
| `uart` | UART 0 interface for the RYLR998 |
| `rotary` | `RotaryIRQ` object used to read the encoder |
| `rbtn` | Encoder pushbutton input on GPIO 8 |
| `btn` | Reset button input on GPIO 9 |
| `current_val` | Previous encoder value, used to detect selection changes |
| `new_val` | Current encoder value read in the main loop |

## Resources and Third-Party Libraries

### `rotary.py`

- **Purpose:** Platform-independent MicroPython rotary encoder state-machine implementation.
- **Source:** [Mike Teachman's micropython-rotary](https://github.com/MikeTeachman/micropython-rotary)
- **Use in VENATOR:** Provides the base `Rotary` class and encoder state-transition logic.
- **License:** MIT, as stated in the source file.
- **Project modifications:** No modifications are reported by the project.

### `rotary_irq_rp2.py`

- **Purpose:** Raspberry Pi Pico/RP2-specific rotary encoder implementation using GPIO interrupts.
- **Source:** [Mike Teachman's micropython-rotary](https://github.com/MikeTeachman/micropython-rotary)
- **Use in VENATOR:** Provides the `RotaryIRQ` class used by `main.py`.
- **Configuration:** CLK GPIO 6, DT GPIO 7, bounded range `0`–`2`, and internal pull-ups enabled.
- **License:** MIT, as stated in the source file.
- **Project modifications:** No modifications are reported by the project.

### `ssd1309.py`

- **Purpose:** I²C driver for the project's 128 × 64 SSD1309 OLED display.
- **Origin:** Adapted from the MicroPython SSD1306 OLED driver approach, with SSD1309-specific initialization and display-control commands.
- **Use in VENATOR:** Provides the `SSD1309_I2C` class used to initialize the display, draw through a framebuffer, and refresh the OLED.
- **Implementation:** Uses a `framebuf.FrameBuffer` object and I²C writes to send commands and display data to the SSD1309 controller.
- **Maintainer:** David Ritter.
- **License:** Confirm and document the applicable license for the original driver and this modified version before redistribution.

## Current Limitations and Next Steps

- **Telemetry:** The OLED shows placeholder coordinates; live telemetry reception and parsing are not implemented in the code documented here.
- **Command confirmation:** The firmware sends command text but does not establish that the drone executed a command.
- **Radio response validation:** `initialize_lora()` sends configuration commands but does not verify each response before continuing.
- **Button handling:** Polling and delays can be improved with more robust debounce and non-blocking handling.
- **Error handling:** UART timeouts, malformed responses, and radio-link failures could be handled more explicitly.
- **Safety:** `Takeoff` and `Go Home` are command strings. Their actual behavior depends on the receiving drone-side firmware and should be tested in a safe, controlled environment.

## References

- [RYLR998 / RYLR498 AT Command User Manual](https://reyax.com/upload/products_download/download_file/LoRa_AT_Command_RYLR998_RYLR498_EN.pdf)
- [Mike Teachman's micropython-rotary](https://github.com/MikeTeachman/micropython-rotary)
- [Raspberry Pi Pico SSD1306 OLED MicroPython tutorial](https://randomnerdtutorials.com/raspberry-pi-pico-ssd1306-oled-micropython/)
- [Raspberry Pi Pico documentation](https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008276-DS-2-getting-started-with-pico.pdf)
- [Rotary encoder example for Raspberry Pi Pico](https://core-electronics.com.au/guides/getting-started-with-rotary-encoders-examples-with-raspberry-pi-pico/)

---

*VENATOR Ground Control Station — firmware documentation.*
