# Minimal SSD1306 I2C driver for MicroPython (128x64).
# Standard command set; framebuf-based text/graphics.
import framebuf
import time

SET_CONTRAST       = 0x81
SET_ENTIRE_ON      = 0xA4
SET_NORM_INV       = 0xA6
SET_DISP           = 0xAE
SET_MEM_ADDR       = 0x20
SET_COL_ADDR       = 0x21
SET_PAGE_ADDR      = 0x22
SET_DISP_START_LINE= 0x40
SET_SEG_REMAP      = 0xA0
SET_MUX_RATIO      = 0xA8
SET_COM_OUT_DIR    = 0xC0
SET_DISP_OFFSET    = 0xD3
SET_COM_PIN_CFG    = 0xDA
SET_DISP_CLK_DIV   = 0xD5
SET_PRECHARGE      = 0xD9
SET_VCOM_DESEL     = 0xDB
SET_CHARGE_PUMP    = 0x8D

class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x80, cmd]))

    def write_data(self, buf):
        self.i2c.writeto(self.addr, b'\x40' + buf)

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,            # off
            SET_MEM_ADDR, 0x00,         # horizontal
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,       # column 127 -> SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,     # scan from COM[N-1] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0xF1,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP, 0x14,
            SET_DISP | 0x01):          # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def contrast(self, value):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(value & 0xFF)

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def show(self):
        x0, x1 = 0, self.width - 1
        if self.width == 64:
            x0, x1 = 32, 95
        self.write_cmd(SET_COL_ADDR); self.write_cmd(x0); self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR); self.write_cmd(0); self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)
