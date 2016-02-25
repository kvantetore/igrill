class DeviceForwardingDelegate(object):
    def __init__(self):
        self.handlers = []

    def handleNotification(self, cHandle, data):
        pass

    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        for handler in self.handlers:
            handler.handleDiscovery(scanEntry, isNewDev, isNewData)


