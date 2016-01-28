#!/usr/bin/env python

import time
import sys
from peripherals import find_peripheral, IGrillMiniPeripheral, UUIDS


if __name__ == "__main__":
    while True:
        try:
            if len(sys.argv) > 1:
                #if we have a command line argument, treat it as device address
                peripheral = IGrillMiniPeripheral(sys.argv[1])
            else:
                #otherwise scan for ble device
                print "Scanning for devices..."
                peripheral = find_peripheral()
                print "Found ", peripheral.addr

            #find characteristics for battery and temperature
            battery_char = peripheral.characteristic(UUIDS.BATTERY_LEVEL)
            temp_char = peripheral.characteristic(UUIDS.PROBE1_TEMPERATURE)

            #poll battery level in order to detect device disconnection
            while True:
                battery_data = battery_char.read()
                battery_level = ord(battery_data[0])

                temp_data = temp_char.read()
                temp = ord(temp_data[0])

                print "Battery:", battery_level
                print "Temp:", temp

                time.sleep(1)

        except RuntimeError as ex:
            print "Error:", ex, ", reconnecting"
            peripheral = None
