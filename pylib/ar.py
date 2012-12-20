# Copyright (c) 2007 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

class Error(Exception):
    pass

class ArHeader:
    FIELDS = ( ('filename', 16),
               ('time', 12),
               ('uid', 6),
               ('gid', 6),
               ('mode', 8),
               ('size', 10),
               ('magic', 2) )

    MAGIC = "\140\012"
    LEN = sum([ field[1] for field in FIELDS ])
               
    def __init__(self, header):
        if len(header) != self.LEN:
            raise Error("illegal header length")

        offset = 0
        fields = {}
        for field in self.FIELDS:
            field_name, field_len = field

            field_value = header[offset:offset + field_len]
            fields[field_name] = field_value

            offset += field_len

        if fields['magic'] != self.MAGIC:
            raise Error("illegal header")

        self.filename = fields['filename'].rstrip()
        for field in ('time', 'uid', 'gid', 'mode', 'size'):
            value = int(fields[field])
            setattr(self, field, value)

class Ar:
    MAGIC="!<arch>\n"
    MAGIC_LEN = len(MAGIC)
    
    def __init__(self, path):
        str = file(path).read(self.MAGIC_LEN)
        if str != self.MAGIC:
            raise Error("illegal ar file (%s)" % path)

        self.path = path

    def extract(self, member):
        """Extracts <member> from filename -> str"""
        fh = file(self.path)
        fh.seek(self.MAGIC_LEN)

        while True:
            str = fh.read(ArHeader.LEN)
            if not str:
                break
            header = ArHeader(str)
            if header.filename == member:
                return fh.read(header.size)

            fh.seek(header.size, 1)

        raise Error("no such member '%s' in archive" % member)

def _extract(archive, member):
    return Ar(archive).extract(member)

# equivalent to _extract but optimized (3X faster)
def _extract_optimized(path, member):
    fh = file(path)
    fh.seek(8)

    while True:
        header = fh.read(60)
        if not header:
            break
        
        if len(header) != 60:
            raise Error("illegal header length")

        offset = 0
        filename = header[:16].rstrip()
        size = int(header[48:-2])

        if filename == member:
            return fh.read(size)

        fh.seek(size, 1)

    raise Error("no such member '%s' in archive" % member)

extract = _extract_optimized
    

