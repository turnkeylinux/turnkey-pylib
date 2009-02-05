import os
from os.path import *
import sha

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
        digest = sha.sha(key).hexdigest()
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
    
