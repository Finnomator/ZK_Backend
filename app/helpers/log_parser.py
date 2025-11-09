import re
from datetime import datetime, timezone, timedelta

from app.models.log import LogEntryDB, char_to_logging_level, LoggingLevel

LOG_REGEX = re.compile(r"^\[(.+)]\[(.)] (.+)$", re.MULTILINE)


class TimeCalibrationMessage:
    __VERSION_REGEX = re.compile(r"Time \((v\d\.\d\.\d)\): ")
    __MSG_REGEX: re.Pattern[str]

    _level: LoggingLevel
    _timestamp: datetime
    _msg: str

    _millis: int

    def __init__(self, timestamp: datetime, level: LoggingLevel, msg: str):
        self._timestamp = timestamp
        self._level = level
        self._msg = msg

    @staticmethod
    def is_calib_msg(msg: str):
        return TimeCalibrationMessage.__VERSION_REGEX.match(msg) is not None

    @staticmethod
    def from_msg(timestamp: datetime, level: LoggingLevel, msg: str):
        match = TimeCalibrationMessage.__VERSION_REGEX.match(msg)

        if match is None:
            raise ValueError()

        version = match.group(1)

        if version == "v1.0.0":
            return V1_0_0(timestamp, level, msg)
        else:
            raise NotImplemented()

    @property
    def millis(self):
        return self._millis


class V1_0_0(TimeCalibrationMessage):
    # example: [2025-10-11T08:57:40.014Z][I] Time (v1.0.0): millis: 11799 ms, Localtime: 25/10/11,10:57:40+08, Unix timestamp: 1760173060, system time: 1760173060013 ms

    __MSG_REGEX = re.compile(
        r"Time \((v\d\.\d\.\d)\): millis: (\d+) ms, Localtime: (.*), Unix timestamp: (\d+), system time: (\d+) ms")

    localtime: str
    unix_timestamp: int
    system_time: int

    def __init__(self, timestamp: datetime, level: LoggingLevel, msg: str):
        super().__init__(timestamp, level, msg)

        result = self.__MSG_REGEX.match(msg)

        if result is None:
            raise ValueError()

        _, raw_millis, self.localtime, raw_unix_timestamp, raw_system_time = result.groups()
        self._millis = int(raw_millis)
        self.unix_timestamp = int(raw_unix_timestamp)
        self.system_time = int(raw_system_time)


def parse_iso(iso_str: str) -> datetime:
    # Example input: "2024-10-12T15:21:39.123Z"
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_log(raw_log: str, imei: str, upload_time: datetime) -> list[LogEntryDB]:
    entries: list[LogEntryDB] = []

    raw_log = raw_log.replace("\r\n", "\n").replace("\r", "\n") # for regex multiline

    for match in LOG_REGEX.finditer(raw_log):
        raw_timestamp, raw_level, msg = match.groups()
        dt_utc = parse_iso(raw_timestamp)
        level = char_to_logging_level(raw_level)

        if dt_utc.year >= 2025 and TimeCalibrationMessage.is_calib_msg(msg):
            calib_msg = TimeCalibrationMessage.from_msg(dt_utc, level, msg)

            calib_millis = calib_msg.millis
            index = len(entries)

            # Set timestamps of entries that have millis timestamp
            found_millis_start = False
            for i in range(index - 1, -1, -1):
                entry = entries[i]
                if entry.timestamp.year >= 2025:
                    if found_millis_start:
                        break
                    continue
                found_millis_start = True
                delta = calib_millis - entry.timestamp.timestamp() * 1000.0
                entry.timestamp = dt_utc - timedelta(milliseconds=delta)
                entry.timestamp_is_valid = 2025 <= dt_utc.year < 2070

        entry = LogEntryDB(imei=imei, timestamp=dt_utc, level=level, message=msg,
                           timestamp_is_valid=2025 <= dt_utc.year < 2070, upload_timestamp=upload_time)
        entries.append(entry)

    return entries
