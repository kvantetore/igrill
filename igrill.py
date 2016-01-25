#!/usr/bin/env python

# bluetooth low energy scan
from bluetooth.ble import GATTRequester, DiscoveryService

from Crypto.Cipher import AES
import random

import time

DEVICE_NAME = "iGrill Mini"
HANDLE_APP_CHALLENGE = 0x0024
HANDLE_DEVICE_CHALLENGE = 0x0026
HANDLE_DEVICE_RESPONSE = 0x0028

HANDLE_READ_TEMPERATURE = 0x0034
HANDLE_NOTIFICATION_TEMPERATURE = 0x0034

HANDLE_BATTERY_LEVEL = 0x0042


def encrypt(key, data):
    return AES.new(key).encrypt(data)


def decrypt(key, data):
    return AES.new(key).decrypt(data)


def find_device_address():
    service = DiscoveryService()
    while True:
        devices = service.discover(2)
        for address, name in devices.items():
            periheral = GATTRequester(address)
            name2 = periheral.read_by_uuid("00002a00-0000-1000-8000-00805f9b34fb")[0]

            print("Found ", address, name, name2)

            if name2.startswith("iGrill Mini"):
                return address


class IDeviceRequester(GATTRequester):
    def __init__(self, address):
        """
        Connects to the device given by address performing necessary authentication
        """
        # connect with pairing, otherwise the device refuses to authenticate
        super(IDeviceRequester, self).__init__(address, False)
        self.connect(security_level="medium")

        # authenticate with idevices custom challenge/response protocol
        if not self.authenticate():
            raise RuntimeError("Unable to authenticate with device")

    def authenticate(self):
        print "Authenticating..."
        # encryption key used by igrill mini
        key = "".join([chr((256 + x) % 256) for x in [-19, 94, 48, -114, -117, -52, -111, 19, 48, 108,
                                                      -44, 104, 84, 21, 62, -35]])

        # send app challenge
        challenge = str(bytearray([(random.randint(0, 255)) for i in range(8)] + [0] * 8))
        self.write_by_handle(HANDLE_APP_CHALLENGE, challenge)

        # read device challenge
        encrypted_device_challenge = self.read_by_handle(HANDLE_DEVICE_CHALLENGE)[0]
        print "encrypted device challenge:", str(encrypted_device_challenge).encode("hex")
        device_challenge = decrypt(key, encrypted_device_challenge)
        print "decrypted device challenge:", str(encrypted_device_challenge).encode("hex")

        # verify device challenge
        if device_challenge[:8] != challenge[:8]:
            return False

        # send device response
        device_response = chr(0) * 8 + device_challenge[8:]
        print "device response: ", str(device_response).encode("hex")
        encrypted_device_response = encrypt(key, device_response)
        self.write_by_handle(HANDLE_DEVICE_RESPONSE, encrypted_device_response)

        print("Authenticated")

        return True

    def on_notification(self, handle, data):
        print "Got notification ", handle, ", ", str(data).encode("hex")
        print "Temperature: ", ord(data[3])


if __name__ == "__main__":
    while True:
        try:
            #find igrill device
            print "Scanning for devices..."
            address = find_device_address()
            print "Found ", address
            peripheral = IDeviceRequester(address)

            # avoid subscribing to notification. it only crashes
            peripheral.write_by_handle(0x0035, '\1\0')

            #poll battery level in order to detect device disconnection
            while True:
                battery_data = peripheral.read_by_handle(HANDLE_BATTERY_LEVEL)[0]
                battery_level = ord(battery_data[0])
                print "Battery:", battery_level
                time.sleep(10)
        except RuntimeError as ex:
            print "Error:", ex, ", reconnecting"
            peripheral = None
