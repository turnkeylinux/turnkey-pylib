"""
Safely create temporary file or directory which is automatically removed
when the object is dereferenced (by the same process that created it,
not a subprocess)
"""
import os
import tempfile
import shutil

class TempFile(file):
    def __init__(self, prefix='tmp', suffix=''):
        fd, path = tempfile.mkstemp(suffix, prefix)
        os.close(fd)
        self.path = path
        self.pid = os.getpid()
        file.__init__(self, path, "w")

    def __del__(self):
        if self.pid == os.getpid():
            os.remove(self.path)

class TempDir:
    def __init__(self, prefix='tmp', suffix='', dir=None):
        self.path = tempfile.mkdtemp(suffix, prefix, dir)
        self.pid = os.getpid()

    def remove(self):
        shutil.rmtree(self.path)
        
    def __del__(self):
        if self.pid == os.getpid():
            self.remove()
