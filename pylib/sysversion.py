# Copyright (c) 2010 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import os
import re
import executil

def _parse_turnkey_release(version):
    m = re.match(r'turnkey-.*?-(\d.*?)-[^\d]', version)
    if m:
        return m.group(1)

def get_turnkey_release():
    """Return release_version. On error, returns None"""
    try:
        version = file("/etc/turnkey_version").read().strip()
        return _parse_turnkey_release(version)

    except IOError:
        pass

def fmt_base_distribution():
    """Return a formatted distribution string:
        e.g., Ubuntu 8.04 Hardy LTS"""

    try:
        output = executil.getoutput("lsb_release -ircd")
    except executil.ExecError:
        return

    d = dict([ line.split(':\t') 
               for line in output.splitlines() ])

    codename = d['Codename'].capitalize()
    basedist = "%s %s %s" % (d['Distributor ID'],
                             d['Release'],
                             d['Codename'].capitalize())
    if d['Codename'] in ('hardy', 'lucid'):
        basedist += " LTS"

    return basedist

def fmt_sysversion():
    version = []
    release = get_turnkey_release()
    if release:
        version.append("TurnKey Linux %s" % release)

    basedist = fmt_base_distribution()
    if basedist:
        version.append(basedist)

    return ' / '.join(version)
