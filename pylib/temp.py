import os
import tempfile
import shutil

class TempFile(file):
    def __init__(self, prefix='tmp', suffix=''):
        fd, path = tempfile.mkstemp(suffix, prefix)
        os.close(fd)
        self.path = path
        file.__init__(self, path, "w")

    def __del__(self):
        os.remove(self.path)

class TempDir:
    def __init__(self, prefix='tmp', suffix='', dir=None):
        self.path = tempfile.mkdtemp(suffix, prefix, dir)

    def remove(self):
        shutil.rmtree(self.path)
        
    def __del__(self):
        self.remove()

        
        
        

