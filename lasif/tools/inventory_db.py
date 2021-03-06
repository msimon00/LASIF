#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple query functions for the inventory database.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2013
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
import re
import requests
import sqlite3
import time


CREATE_DB_SQL = """
CREATE TABLE IF NOT EXISTS stations(
    station_name TEXT,
    latitude REAL,
    longitude REAL,
    elevation REAL,
    depth REAL
);"""


URL = ("http://service.iris.edu/fdsnws/station/1/query?"
    "network={network}&sta={station}&level=station&nodata=404")


class InventoryDB(object):
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute(CREATE_DB_SQL)
        self.conn.commit()

    def __del__(self):
        try:
            self.conn.close()
        except:
            pass

    def put_station_coordinates(self, station_id, latitude, longitude,
            elevation_in_m, depth_in_m):
        latitude = str(latitude) if latitude is not None else "NULL"
        longitude = str(longitude) if longitude is not None else "NULL"
        elevation_in_m = str(elevation_in_m) \
            if elevation_in_m is not None else "NULL"
        depth_in_m = str(depth_in_m) if depth_in_m is not None else "NULL"

        SQL = """
        REPLACE INTO stations
            (station_name, latitude, longitude, elevation, depth)
        VALUES ('%s', %s, %s, %s, %s);
        """ % (station_id, latitude, longitude, elevation_in_m, depth_in_m)
        self.cursor.execute(SQL)
        self.conn.commit()


def get_station_coordinates(db_file, station_id):
    """
    Returns either a dictionary containing "latitude", "longitude",
    "elevation_in_m", "local_depth_in_m" keys or None if nothing was found.
    """
    inv_db = InventoryDB(db_file)

    SQL = """
    SELECT latitude, longitude, elevation, depth
    FROM stations
    WHERE station_name = '%s'
    LIMIT 1;
    """ % station_id
    coordinates = inv_db.cursor.execute(SQL).fetchone()

    if coordinates and coordinates[0] is None:
        return None

    elif coordinates:
        return {"latitude": coordinates[0], "longitude": coordinates[1],
            "elevation_in_m": coordinates[2],
            "local_depth_in_m": coordinates[3]}

    msg = ("Attempting to download coordinates for %s. This will only "
        "happen once ... ") % station_id
    print msg,
    # Otherwise try to download the necessary information.
    network, station = station_id.split(".")
    for _i in xrange(10):
        try:
            req = requests.get(URL.format(network=network, station=station))
            break
        except:
            time.sleep(0.1)
    if str(req.status_code)[0] != "2":
        print "Failure."
        inv_db.put_station_coordinates(station_id, None, None, None, None)
        return None

    # Now simply find the coordinates.
    lat = float(re.findall("<Latitude>(.*)</Latitude>", req.text)[0])
    lng = float(re.findall("<Longitude>(.*)</Longitude>", req.text)[0])
    ele = float(re.findall("<Elevation>(.*)</Elevation>", req.text)[0])

    inv_db.put_station_coordinates(station_id, lat, lng, ele, None)
    print "Success."
    return {"latitude": lat, "longitude": lng, "elevation_in_m": ele,
        "local_depth_in_m": 0.0}
