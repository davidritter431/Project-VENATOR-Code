# SSD1309 MicroPython I2C OLED Driver
# For 128x64 SSD1309 displays
#
# Designed for:
# Raspberry Pi Pico / RP2040
# 2.42" 128x64 SSD1309 I2C OLED
#
# I2C:
# SDA -> GPIO 4
# SCL -> GPIO 5
#
# David Ritter
# 9/15/2026

from micropython import const
import framebuf
import time


# ---------------------------------------------------------
# SSD1309 Commands
# ---------------------------------------------------------

SET_CONTRAST = const(0x81)
SET_DISPLAY = const(0xA4)
SET_NORMAL_DISPLAY = const(0xA6)
SET_INVERSE_DISPLAY = const(0xA7)

DISPLAY_OFF = const(0xAE)
DISPLAY_ON = const(0xAF)

SET_DISPLAY_OFFSET = const(0xD3)
SET_START_LINE = const(0x40)

SET_SEGMENT_REMAP = const(0xA1)

SET_MULTIPLEX = const(0xA8)

SET_COM_SCAN_DIRECTION = const(0xC8)

SET_COM_PINS = const(0xDA)

SET_DISPLAY_CLOCK = const(0xD5)

SET_PRECHARGE = const(0xD9)

SET_VCOM_DESELECT = const(0xDB)

SET_MEMORY_MODE = const(0x20)

SET_COLUMN_ADDRESS = const(0x21)
SET_PAGE_ADDRESS = const(0x22)


# ---------------------------------------------------------
# SSD1309 I2C Driver
# ---------------------------------------------------------

class SSD1309_I2C:

    def __init__(self, width, height, i2c, addr=0x3C):

        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr

        # Number of pages
        self.pages = height // 8

        # Display buffer
        self.buffer = bytearray(width * self.pages)

        # Create framebuffer
        self.framebuf = framebuf.FrameBuffer(
            self.buffer,
            width,
            height,
            framebuf.MONO_VLSB
            )

        # I2C command/data buffers
        self.temp = bytearray(2)

        self.write_list = [
            b"\x40",
            None
        ]

        # Initialize display
        self.init_display()


    # -----------------------------------------------------
    # Send a command to the SSD1309
    # -----------------------------------------------------

    def write_cmd(self, cmd):

        self.temp[0] = 0x80
        self.temp[1] = cmd

        self.i2c.writeto(self.addr, self.temp)


    # -----------------------------------------------------
    # Send display data to the SSD1309
    # -----------------------------------------------------

    def write_data(self, buf):

        self.write_list[1] = buf

        self.i2c.writevto(
            self.addr,
            self.write_list
        )


    # -----------------------------------------------------
    # Initialize SSD1309
    # -----------------------------------------------------

    def init_display(self):

        # Turn display OFF
        self.write_cmd(DISPLAY_OFF)

        # Memory addressing mode
        #
        # 0x00 = horizontal addressing
        #
        self.write_cmd(SET_MEMORY_MODE)
        self.write_cmd(0x00)

        # Display start line = 0
        self.write_cmd(SET_START_LINE)

        # Segment remap
        #
        # Maps column 127 to segment 0
        #
        self.write_cmd(SET_SEGMENT_REMAP)

        # Multiplex ratio
        #
        # 128x64 = 64 rows
        # 64 - 1 = 63
        #
        self.write_cmd(SET_MULTIPLEX)
        self.write_cmd(0x3F)

        # Display offset = 0
        self.write_cmd(SET_DISPLAY_OFFSET)
        self.write_cmd(0x00)

        # COM scan direction
        self.write_cmd(SET_COM_SCAN_DIRECTION)

        # COM pins configuration
        #
        # 0x12 is typical for 128x64
        #
        self.write_cmd(SET_COM_PINS)
        self.write_cmd(0x12)

        # Display clock divide ratio / oscillator
        self.write_cmd(SET_DISPLAY_CLOCK)
        self.write_cmd(0x80)

        # Pre-charge period
        self.write_cmd(SET_PRECHARGE)
        self.write_cmd(0xF1)

        # VCOMH deselect level
        self.write_cmd(SET_VCOM_DESELECT)
        self.write_cmd(0x40)

        # Contrast
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(0xFF)

        # Entire display follows RAM
        self.write_cmd(SET_DISPLAY)

        # Normal display
        self.write_cmd(SET_NORMAL_DISPLAY)

        # Clear framebuffer
        self.framebuf.fill(0)

        # Turn display ON
        self.write_cmd(DISPLAY_ON)

        # Give display time to stabilize
        time.sleep_ms(100)


    # -----------------------------------------------------
    # Refresh display
    # -----------------------------------------------------

    def show(self):

        # Set column address range
        self.write_cmd(SET_COLUMN_ADDRESS)
        self.write_cmd(0)
        self.write_cmd(self.width - 1)

        # Set page address range
        self.write_cmd(SET_PAGE_ADDRESS)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)

        # Send framebuffer
        self.write_data(self.buffer)


    # -----------------------------------------------------
    # Turn display OFF
    # -----------------------------------------------------

    def poweroff(self):

        self.write_cmd(DISPLAY_OFF)


    # -----------------------------------------------------
    # Turn display ON
    # -----------------------------------------------------

    def poweron(self):

        self.write_cmd(DISPLAY_ON)


    # -----------------------------------------------------
    # Set contrast
    # -----------------------------------------------------

    def contrast(self, contrast):

        if contrast < 0:
            contrast = 0

        if contrast > 255:
            contrast = 255

        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)


    # -----------------------------------------------------
    # Normal / inverted display
    # -----------------------------------------------------

    def invert(self, invert):

        if invert:
            self.write_cmd(SET_INVERSE_DISPLAY)

        else:
            self.write_cmd(SET_NORMAL_DISPLAY)


    # -----------------------------------------------------
    # Reset framebuffer
    # -----------------------------------------------------

    def clear(self):

        self.framebuf.fill(0)
        self.show()

