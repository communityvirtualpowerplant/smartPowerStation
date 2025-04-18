# Adafruit INA260
# source: https://learn.adafruit.com/adafruit-ina260-current-voltage-power-sensor-breakout/python-circuitpython
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

'''
Default Address for Adafruit's INA260 is 40
If these pins are soldered the address is as follows:
A0 = 1000001 = 41
A1 = 1000100 = 44 = 0x2C
A0 & A1 = 1000101 =45 
INA260 datasheet w/ Address Table: https://www.ti.com/lit/ds/symlink/ina260.pdf 
'''

import board
import busio

# scan all I2C Devices
# source: https://learn.adafruit.com/circuitpython-basics-i2c-and-spi/i2c-devices
REGISTERS = (0, 256) # Range of registers to read from
REGISTER_SIZE = 2 #Number of bytes to read from each register

# Initialize
i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
    pass

devices = i2c.scan()
while len(devices) < 1:
    devices = i2c.scan()

[print(hex(d)) for d in devices]
