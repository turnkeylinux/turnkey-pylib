# Copyright (c) 2007 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
import subprocess

class Error(Exception):
    pass

class Ar:
    def __init__(self, path):
        self.path = path

    def list(self):
        contents = subprocess.check_output(['ar', '-t', self.path])
        return [line.strip() for line in contents.decode().split('\n')]

    def extract(self, member):
        return subprocess.check_output(['ar', '-p', self.path, member])

def _extract(archive, member):
    return Ar(archive).extract(member)

def _list(path):
    return Ar(path).list()

extract = _extract
list = _list
