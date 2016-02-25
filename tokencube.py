

class TokenCubeHandler(object):
    def __init__(self, device_settings):
        self.device_settings = device_settings
        self.devices = {}


    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        data = bytearray(scanEntry.scanData.get(255, []))

        #print "Handling", data

        # make sure we have a tokencube device
        if len(data) < 7 or data[0] != 0xee or data[1] != 0xff:
            return

        dev = self.devices.get(scanEntry.addr, None)
        if dev is None:
            dev = self.devices[scanEntry.addr] = {}

        #read sensor data
        sensor_index = 5
        while sensor_index < len(data):
            sensor = data[sensor_index]
            if sensor == 0x01 or sensor == 0x81:
                dev["temperature"] = get_float(data, sensor_index + 1, 2)
                sensor_index += 3
            elif sensor == 0x04 or sensor == 0x84:
                dev["humidity"] = get_float(data, sensor_index + 1, 2)
                sensor_index += 3
            elif sensor == 0x05 or sensor == 0x85:
                dev["pressure"] = get_float(data, sensor_index + 1, 4)
                sensor_index += 5
            elif sensor == 0x06 or sensor == 0x86:
                dev["orientation_x"] = get_int(data, sensor_index + 1, 2)
                dev["orientation_y"] = get_int(data, sensor_index + 3, 2)
                dev["orientation_z"] = get_int(data, sensor_index + 5, 2)
                sensor_index += 7
            elif sensor == 0x07 or sensor == 0x87:
                dev["pir_motion"] = data[sensor_index + 1]
                sensor_index += 2
            elif sensor == 0x08 or sensor == 0x88:
                dev["sensor_motion"] = data[sensor_index + 1]
                sensor_index += 2
            elif sensor == 0x09 or sensor == 0x89:
                dev["shock_x"] = data[sensor_index + 1]
                dev["shock_y"] = data[sensor_index + 2]
                dev["shock_z"] = data[sensor_index + 3]
                sensor_index += 4
            elif sensor == 0x0A or sensor == 0x8A:
                dev["battery"] = float(data[sensor_index + 1])
                sensor_index += 2
            else:
                print "Unknown sensor", sensor, "at index", sensor_index, "data = ", [x for x in data]
                break

        print "Got sensor data:", dev

    def persist_stats(self, persistence):
        for addr, stats in self.devices.items():
            settings = self.device_settings.get(addr, None)
            if settings is None:
                settings = {
                    "name": "TokenCube " + addr,
                    "tags": {
                        "addr": addr,
                        "type": "ambient"
                    }
                }

            device_name = settings["name"]
            tags = settings["tags"]

            if "temperature" in stats:
                persistence.save_temperature(stats["temperature"], device_name, **tags)

            if "battery" in stats:
                persistence.save_battery_level(stats["battery"], device_name, **tags)


def get_float(data, offset, length):
    return get_int(data, offset, length) / 100.0

def get_int(data, offset, length):
    ret = 0
    for i in range(length):
        ret = ret + data[offset + length - i - 1] * 255**i
    return ret