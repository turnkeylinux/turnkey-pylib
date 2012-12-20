# Copyright (c) 2007 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import os
from os.path import *
from hashlib import sha1

class Error(Exception):
    pass

class HashStore:
    """Hash storage class, which maintains arbitrary string key/values in
    a plain directory structure."""
    def __init__(self, path):
        if not isdir(path):
            raise Error("not a directory (%s)" % path)
        self.path = realpath(path)

    def _get_path(self, key):
        digest = sha1(key).hexdigest()
        return join(self.path, digest[:2], digest[2:])

    def get(self, key):
        path = self._get_path(key)
        if not exists(path):
            return None
        val = file(path).read()
        if not val:
            return None
        return val


    def set(self, key, value):
        path = self._get_path(key)
        if not exists(dirname(path)):
            os.makedirs(dirname(path))

        file(path, "w").write(str(value))

    def exists(self, key):
        path = self._get_path(key)
        if exists(path):
            return True
        return False

    def delete(self, key):
        path = self._get_path(key)
        if not exists(path):
            return
        
        os.remove(path)

        # delete empty hash storage directories
        if not os.listdir(dirname(path)):
            os.rmdir(dirname(path))
        
    def __len__(self):
        count = 0
        for fname in os.listdir(self.path):
            if len(fname) != 2:
                continue
            
            fpath = join(self.path, fname)
            if not isdir(fpath):
                continue
            count += len(os.listdir(fpath))
            
        return count

    def __nonzero__(self):
        return True

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        if not self.exists(key):
            raise KeyError(key)
        
        self.delete(key)

def test():
    hs = HashStore("/sterile/tmp/hashstore")
    hs['foo'] = 'bar'
    print hs['foo']

    print len(hs)
    del hs['foo']
    print len(hs)
             
if __name__=="__main__":
    test()
    
