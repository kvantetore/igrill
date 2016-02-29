import bluepy.btle as btle
import random

from crypto import encrypt, decrypt

class UUIDS:
    FIRMWARE_VERSION   = btle.UUID("64ac0001-4a4b-4b58-9f37-94d3c52ffdf7")

    BATTERY_LEVEL      = btle.UUID(0x2a19)

    APP_CHALLENGE      = btle.UUID("64ac0002-4a4b-4b58-9f37-94d3c52ffdf7")
    DEVICE_CHALLENGE   = btle.UUID("64ac0003-4a4b-4b58-9f37-94d3c52ffdf7")
    DEVICE_RESPONSE    = btle.UUID("64ac0004-4a4b-4b58-9f37-94d3c52ffdf7")

    CONFIG             = btle.UUID("06ef0002-2e06-4b79-9e33-fce2c42805ec")
    PROBE1_TEMPERATURE = btle.UUID("06ef0002-2e06-4b79-9e33-fce2c42805ec")
    PROBE1_THRESHOLD   = btle.UUID("06ef0003-2e06-4b79-9e33-fce2c42805ec")
    PROBE2_TEMPERATURE = btle.UUID("06ef0004-2e06-4b79-9e33-fce2c42805ec")
    PROBE2_THRESHOLD   = btle.UUID("06ef0005-2e06-4b79-9e33-fce2c42805ec")
    PROBE3_TEMPERATURE = btle.UUID("06ef0006-2e06-4b79-9e33-fce2c42805ec")
    PROBE3_THRESHOLD   = btle.UUID("06ef0007-2e06-4b79-9e33-fce2c42805ec")
    PROBE4_TEMPERATURE = btle.UUID("06ef0008-2e06-4b79-9e33-fce2c42805ec")
    PROBE4_THRESHOLD   = btle.UUID("06ef0009-2e06-4b79-9e33-fce2c42805ec")


class IGrillHandler(object):
    def __init__(self, device_settings):
        self.device_settings = device_settings
        self.devices = []


    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        name = scanEntry.getValueText(8)
        if name != "iGrill_mini" or not isNewDev:
            return

        #see if we have this device already
        for d in self.devices:
            if d.addr == scanEntry.addr:
                return

        #add dev
        dev = IGrillMiniPeripheral(d.addr)
        self.devices.append(dev)

    def persist_stats(self, persistence):
        for dev in self.devices:
            settings = self.device_settings.get(dev.addr)
            if settings == None:
                settings = {
                    "device": "iGrill " + dev.addr,
                    "type": "kitchen",
                    "addr": dev.addr,
                }

            temp = dev.read_temperature()
            fields = {"temperature": temp}
            persistence.save("sensordata", fields, **settings)

            battery = dev.read_battery()
            persistence.save_temperature(battery, **settings)


class IDevicePeripheral(btle.Peripheral):
    encryption_key = None

    def __init__(self, address):
        """
        Connects to the device given by address performing necessary authentication
        """
        btle.Peripheral.__init__(self, address)

        # iDevice devices require bonding. I don't think this will give us bonding
        # if no bonding exists, so please use bluetoothctl to create a bond first
        self.setSecurityLevel("medium")

        # enumerate all characteristics so we can look up handles from uuids
        self.characteristics = self.getCharacteristics()

        # authenticate with iDevices custom challenge/response protocol
        if not self.authenticate():
            raise RuntimeError("Unable to authenticate with device")

    def characteristic(self, uuid):
        """
        Returns the characteristic for a given uuid.
        """
        for c in self.characteristics:
            if c.uuid == uuid:
                return c

    def authenticate(self):
        """
        Performs iDevices challenge/response handshake. Returns if handshake succeeded

        """
        print "Authenticating..."
        # encryption key used by igrill mini
        key = "".join([chr((256 + x) % 256) for x in self.encryption_key])

        # send app challenge
        challenge = str(bytearray([(random.randint(0, 255)) for i in range(8)] + [0] * 8))
        self.characteristic(UUIDS.APP_CHALLENGE).write(challenge, True)

        # read device challenge
        encrypted_device_challenge = self.characteristic(UUIDS.DEVICE_CHALLENGE).read()
        print "encrypted device challenge:", str(encrypted_device_challenge).encode("hex")
        device_challenge = decrypt(key, encrypted_device_challenge)
        print "decrypted device challenge:", str(device_challenge).encode("hex")

        # verify device challenge
        if device_challenge[:8] != challenge[:8]:
            print "Invalid device challenge"
            return False

        # send device response
        device_response = chr(0) * 8 + device_challenge[8:]
        print "device response: ", str(device_response).encode("hex")
        encrypted_device_response = encrypt(key, device_response)
        self.characteristic(UUIDS.DEVICE_RESPONSE).write(encrypted_device_response, True)

        print("Authenticated")

        return True


class IGrillMiniPeripheral(IDevicePeripheral):
    """
    Specialization of iDevice peripheral for the iGrill Mini (sets the correct encryption key
    """

    # encryption key for the iGrill Mini
    encryption_key = [-19, 94, 48, -114, -117, -52, -111, 19, 48, 108, -44, 104, 84, 21, 62, -35]

    def __init__(self, address):
        IDevicePeripheral.__init__(self, address)

        # find characteristics for battery and temperature
        self.battery_char = self.characteristic(UUIDS.BATTERY_LEVEL)
        self.temp_char = self.characteristic(UUIDS.PROBE1_TEMPERATURE)

    def read_temperature(self):
        return float(ord(self.temp_char.read()[0]))

    def read_battery(self):
        return float(ord(self.battery_char.read()[0]))