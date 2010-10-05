import os
import re
import commands

PATH_TURNKEY_VERSION = "/etc/turnkey_version"

class Error(Exception):
    pass

def get_turnkey_version():
    """Return (codename, release_version)"""
    try:
        version = file(PATH_TURNKEY_VERSION).read().strip()
    except IOError:
        raise Error("no such file '%s'" % PATH_TURNKEY_VERSION)

    m = re.match(r'turnkey-(.*?)-([\d\.]+)', version)
    if not m:
        raise Error("couldn't parse version '%s'" % version)

    codename, version = m.groups()
    return codename, version

def get_lsb_release():
    output = commands.getoutput("lsb_release -ircd")
    return dict([ line.split(':\t') 
                  for line in output.splitlines() ])

def get_basedist():
    d = get_lsb_release()
    codename = d['Codename'].capitalize()
    basedist = "%s %s %s" % (d['Distributor ID'],
                             d['Release'],
                             d['Codename'].capitalize())
    if d['Codename'] in ('hardy', 'lucid'):
        basedist += " LTS"

    return basedist

