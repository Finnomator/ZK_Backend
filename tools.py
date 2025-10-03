import struct
from datetime import datetime
from zoneinfo import ZoneInfo

import gpxpy
import gpxpy.gpx

fmt = '<ffffBBfQ'


def gps_to_gpx(file_path: str, output_path: str):
    struct_size = struct.calcsize(fmt)

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(struct_size)
            if not chunk:
                break
            (lat, lon, speed, alt, vsat, usat, accuracy, unix_timestamp) = struct.unpack(fmt, chunk)

            dt_germany = datetime.fromtimestamp(unix_timestamp, tz=ZoneInfo("Europe/Berlin"))

            point = gpxpy.gpx.GPXTrackPoint(
                latitude=lat,
                longitude=lon,
                elevation=alt,
                time=dt_germany
            )
            gpx_segment.points.append(point)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(gpx.to_xml())


def print_log(file_path: str):
    logging_levels = ["D", "I", "W", "E", "C"]
    with open(file_path, "rb") as f:
        while True:
            # Read timestamp (8 bytes)
            ts_bytes = f.read(8)
            if not ts_bytes:
                break

            timestamp = struct.unpack("<Q", ts_bytes)[0]  # little-endian uint64
            # dt_germany = datetime.fromtimestamp(timestamp, tz=ZoneInfo("Europe/Berlin"))
            # Read level (1 byte)
            level = struct.unpack("<B", f.read(1))[0]
            level_char = logging_levels[level]

            # Read string length (2 bytes)
            length = struct.unpack("<H", f.read(2))[0]

            # Read the string
            text = f.read(length).decode("utf-8", errors="replace")

            print(timestamp, level_char, text)


if __name__ == "__main__":
    ...
