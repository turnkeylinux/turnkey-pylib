# Copyright (c) 2010 Alon Swartz <alon@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import re

import struct
import socket
import fcntl

import executil
from lazyclass import lazyclass

SIOCGIFFLAGS = 0x8913
SIOCGIFADDR = 0x8915 
SIOCGIFNETMASK = 0x891b 
SIOCGIFBRDADDR = 0x8919

IFF_UP = 0x1           # interface is up
IFF_BROADCAST = 0x2    # vald broadcast address
IFF_DEBUG = 0x4        # internal debugging flag
IFF_LOOPBACK = 0x8     # inet is a loopback
IFF_POINTOPOINT = 0x10 # inet is ptp link
IFF_NOTRAILERS = 0x20  # avoid use of trailers
IFF_RUNNING = 0x40     # resources allocated
IFF_NOARP = 0x80       # L2 dest addr not set
IFF_PROMISC = 0x100    # promiscuous mode
IFF_ALLMULTI = 0x200   # get all multicast packets
IFF_MASTER = 0x400     # master of load balancer
IFF_SLAVE = 0x800      # slave of load balancer
IFF_MULTICAST = 0x1000 # supports multicast
IFF_PORTSEL = 0x2000   # can set media type
IFF_AUTOMEDIA = 0x4000 # auto media select active
IFF_DYNAMIC = 0x8000L  # addr's lost on inet down
IFF_LOWER_UP = 0x10000 # has netif_dormant_on()
IFF_DORMANT = 0x20000  # has netif_carrier_on()

def get_ifnames():
    """ returns list of interface names (up and down) """
    ifnames = []
    for line in file('/proc/net/dev').readlines():
        try:
            ifname, junk = line.strip().split(":")
            ifnames.append(ifname)
        except ValueError:
            pass

    return ifnames

class Error(Exception):
    pass

class InterfaceInfo(object):
    """enumerate network related configurations"""

    sockfd = lazyclass(socket.socket)(socket.AF_INET, socket.SOCK_DGRAM)

    FLAGS = { }
    for attr in ('up', 'broadcast', 'debug', 'loopback',
                 'pointopoint', 'notrailers', 'running',
                 'noarp', 'promisc', 'allmulti', 'master',
                 'slave', 'multicast', 'portsel', 'automedia',
                 'dynamic', 'lower_up', 'dormant'):
        FLAGS[attr] = globals()['IFF_' + attr.upper()]

    def __getattr__(self, attrname):
        if attrname.startswith("is_"):
            attrname = attrname[3:]

            if attrname in self.FLAGS:
                try:
                    return self._get_ioctl_flag(self.FLAGS[attrname])
                except IOError:
                    raise Error("could not get %s flag for %s" % (attrname, self.ifname))

        raise AttributeError("no such attribute: " + attrname)

    def __init__(self, ifname):
        if ifname not in get_ifnames():
            raise Error("no such interface '%s'" % ifname)

        self.ifname = ifname
        self.ifreq = (self.ifname + '\0'*32)[:32]

    def _get_ioctl(self, magic):
        return fcntl.ioctl(self.sockfd.fileno(), magic, self.ifreq)

    def _get_ioctl_addr(self, magic):
        try:
            result = self._get_ioctl(magic)
        except IOError:
            return None

        return socket.inet_ntoa(result[20:24])

    def _get_ioctl_flag(self, magic):
        result = self._get_ioctl(SIOCGIFFLAGS)
        flags = struct.unpack('H', result[16:18])[0]
        return (flags & magic) != 0

    @property
    def address(self):
        return self._get_ioctl_addr(SIOCGIFADDR)
    addr = address

    @property
    def netmask(self):
        return self._get_ioctl_addr(SIOCGIFNETMASK)

    @property
    def gateway(self):
        try:
            output = executil.getoutput("route -n")
        except executil.ExecError:
            return None

        for line in output.splitlines():
            m = re.search('^0.0.0.0\s+(.*?)\s+(.*)\s+%s' % self.ifname, line, re.M)
            if m:
                return m.group(1)

        return None

def get_hostname():
    return socket.gethostname()

