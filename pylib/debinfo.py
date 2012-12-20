# Copyright (c) 2007 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

""" This module provides a high-level interface to cached extraction
of control field data from Debian binary packages.  """

import re
import commands
import os
from os.path import *

import pwd
import tarfile
from hashlib import md5
from cStringIO import StringIO

import ar
from hashstore import HashStore

class Error(Exception):
    pass

def _init_debinfo_cache():
    home_dir = pwd.getpwuid(os.getuid()).pw_dir
    debinfo_dir = os.environ.get("DEBINFO_DIR",
                                 join(home_dir, ".debinfo"))
    if not exists(debinfo_dir):
        os.makedirs(debinfo_dir)

    return HashStore(debinfo_dir)

_cache = _init_debinfo_cache()

def _extract_control(path):
    control_tar_gz = ar.extract(path, "control.tar.gz")
    fh = StringIO(control_tar_gz)
    tar = tarfile.open("control.tar.gz", mode="r:gz", fileobj=fh)
    try:
        return tar.extractfile("./control").read()
    except KeyError:
        return tar.extractfile("control").read()

def get_key(path):
    """calculate the debinfo key for a Debian binary package at <path>"""
    return md5(ar.extract(path, "control.tar.gz")).hexdigest()

def get_control_by_key(key):
    """get control data from debinfo cache by <key> -> str"""
    return _cache.get(key)
    
def get_control_by_path(path, usecache=True):
    """get control data from a Debian binary package at <path> -> str (cached)

    If possible, the control file is retrieved from the debinfo cache.
    Otherwise the control file is extracted from the path and stored in the debinfo cache.
    """
    if not usecache:
        return _extract_control(path)
        
    key = get_key(path)
    control = _cache.get(key)
    if control is None:
        control = _extract_control(path)
        _cache.set(key, control)

    return control

def parse_control(control):
    """parse control fields -> dict"""
    d = {}
    for line in control.split("\n"):
        if not line or line[0] == " ":
            continue
        line = line.strip()
        i = line.index(':')
        key = line[:i]
        val = line[i + 2:]
        d[key] = val

    return d

def get_control_fields(path):
    """convenience function which extracts control fields from a Debian binary package -> dict"""
    control = get_control_by_path(path)
    return parse_control(control)

