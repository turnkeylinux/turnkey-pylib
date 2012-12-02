#!/usr/bin/python
# Copyright (c) 2008 Alon Swartz <alon@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import executil

class Device:
    """class to hold device information enumerated from udev database"""
    def __init__(self, s):
        self.path = None
        self.name = None
        self.symlinks = []
        self.env = {}

        self._parse_raw_data(s)

    def _parse_raw_data(self, s):
        for entry in s.splitlines():
            type, value = entry.split(' ', 1)
            type = type.strip(":")

            if type == "P":
                self.path = value
                continue

            if type == "N":
                self.name = value
                continue

            if type == "S":
                self.symlinks.append(value)
                continue

            if type == "E":
                name, val = value.split("=")
                self.env[name] = val

def query(device=None):
    """query udev database and return device(s) information
       if no device is specified, all devices will be returned
    """
    if device:
        cmd = "udevadm info --query all --name %s" % device
    else:
        cmd = "udevadm info --export-db"

    devices = []
    for s in executil.getoutput(cmd).split('\n\n'):
        devices.append(Device(s))

    return devices
    
    
def _disk_devices():
    """debug/test method to print disk devices"""
    devices = query()
    for dev in devices:
        if dev.env.has_key('DEVTYPE') and dev.env['DEVTYPE'] == 'disk':
            print '/dev/' + dev.name

            attrs = dev.env.keys()
            attrs.sort()
            column_len = max([ len(attr) + 1 for attr in attrs ])
            for attr in attrs:
                name = attr + ":"
                print "  %s %s" % (name.ljust(column_len), dev.env[attr])
            print

def main():
   _disk_devices()    #used in debugging/testing

if __name__ == '__main__':
    main()

