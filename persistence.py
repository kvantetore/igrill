from influxdb import InfluxDBClient
import datetime
import pytz


class DataPersistence(object):
    def __init__(self, server, database, username="root", password="root"):
        self.influxClient = InfluxDBClient(server, database=database, username=username, password=password)

    def save_battery_level(self, battery_level_percent, device, **tags):
        tags["device"] = device
        fields = {
            "battery_level_percent": battery_level_percent
        }
        self.save("device_battery", fields, tags)

    def save(self, measurement, fields, tags):

        d = datetime.datetime.now(pytz.utc)
        d = datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)

        self.influxClient.write_points([{
            "measurement": measurement,
            "tags": tags,
            "fields": fields,
            "time": datetime.datetime.utcnow().isoformat()
        }])