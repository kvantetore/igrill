import os
from bluepy.btle import Scanner

from scan import DeviceForwardingDelegate
from persistence import DataPersistence
from igrill import IGrillHandler
from tokencube import TokenCubeHandler

device_settings = {
    "d4:81:ca:03:ab:80": {
        "device": "iGrill Mini",
        "addr": "d4:81:ca:03:ab:80",
        "type": "kitchen"
    },
    "dc:00:62:95:62:67": {
        "device": "TokenCube 1",
        "addr": "dc:00:62:95:62:67",
        "type": "ambient"
    }
}

INFLUX_SERVER = os.environ.get("INFLUX_SERVER", None) or "raspberrypi.local"
INFLUX_DATABASE = os.environ.get("INFLUX_DB", None) or "sensors"
INFLUX_USER = os.environ.get("INFLUX_USER", None) or "root"
INFLUX_PASSWORD = os.environ.get("INFLUX_PASSWORD", None) or "root"

if __name__ == "__main__":
    print "Creating Scanner"
    delegate = DeviceForwardingDelegate()
    delegate.handlers.append(IGrillHandler(device_settings))
    delegate.handlers.append(TokenCubeHandler(device_settings))

    scanner = Scanner()
    scanner.withDelegate(delegate)

    print "Connecting to InfluxDB server"
    persistence = DataPersistence(INFLUX_SERVER, INFLUX_DATABASE, INFLUX_USER, INFLUX_PASSWORD)

    while True:
        print "Scanning..."
        scanner.scan(30)

        print "Persisting..."
        for handler in delegate.handlers:
            handler.persist_stats(persistence)
