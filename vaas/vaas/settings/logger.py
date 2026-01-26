from datetime import datetime
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def formatTime(self, record, datefmt=None):
        # record.created contains the float timestamp
        tstamp = datetime.utcfromtimestamp(record.created)
        return tstamp.isoformat(timespec="milliseconds") + "Z"