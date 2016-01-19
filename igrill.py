# bluetooth low energy scan
from bluetooth.ble import GATTRequester, DiscoveryService
from Crypto.Cipher import AES
import random


DEVICE_NAME = "iGrill Mini"
HANDLE_APP_CHALLENGE = 0x0024
HANDLE_DEVICE_CHALLENGE = 0x0026
HANDLE_DEVICE_RESPONSE = 0x0028

HANDLE_READ_TEMPERATURE = 0x0034


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


def authenticate(periheral):
    print("Authenticating...")
    #encryption key used by igrill mini
    key = "".join([chr((256 + x) % 256) for x in [-19, 94, 48, -114, -117, -52, -111, 19, 48, 108,
                                    -44, 104, 84, 21, 62, -35]])

    #send app challenge
    challenge = str(bytearray([(random.randint(0, 255)) for i in range(8)] + [0] * 8))
    periheral.write_by_handle(HANDLE_APP_CHALLENGE, challenge)

    #read device challenge
    encrypted_device_challenge = periheral.read_by_handle(HANDLE_DEVICE_CHALLENGE)[0]
    print("encrypted device challenge:", str(encrypted_device_challenge).encode("hex"))
    device_challenge = decrypt(key, encrypted_device_challenge)
    print("decrypted device challenge:", str(encrypted_device_challenge).encode("hex"))

    #verify device challenge
    if device_challenge[:8] != challenge[:8]:
        return False

    #send device response
    device_response = chr(0) * 8 + device_challenge[8:]
    print("device response: ", str(device_response).encode("hex"))
    encrypted_device_response = encrypt(key, device_response)
    periheral.write_by_handle(HANDLE_DEVICE_RESPONSE, encrypted_device_response)

    print("Authenticated")

    return True


address = find_device_address()
peripheral = GATTRequester(address, False)
peripheral.connect(security_level="medium")

if not authenticate(peripheral):
    print("Authentication Failed")
    exit(-1)

import time

while True:
    temp_data = peripheral.read_by_handle(HANDLE_READ_TEMPERATURE)[0]
    temp = ord(temp_data[0])
    print("Temp:", temp)
    time.sleep(1)