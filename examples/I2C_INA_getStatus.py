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

import time
import board
import busio
import adafruit_ina260
import adafruit_ina219

# Initialize
i2c = busio.I2C(board.SCL, board.SDA)

ina219 = adafruit_ina219.INA219(i2c_bus = i2c,addr =0x40)
ina260 = adafruit_ina260.INA260(i2c_bus = i2c,address = 0x44)

while True:
    print('')
    print('***  260 ***')
    print(
        "Current: %.2f mA Voltage: %.2f V Power:%.2f mW"
        % (ina260.current, ina260.voltage, ina260.power)
    )

    print('')
    print('*** 219 ***')
    print(
        "Current: %.2f mA Voltage: %.2f V Power:%.2f mW"
        % (ina219.current, ina219.bus_voltage, ina219.power)
    )

    time.sleep(2)
