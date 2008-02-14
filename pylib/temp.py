import os
import tempfile

class TempFile(file):
    def __init__(self, prefix='tmp', suffix=''):
        fd, path = tempfile.mkstemp(suffix, prefix)
        os.close(fd)
        self.path = path
        file.__init__(self, path, "w")

    def __del__(self):
        os.remove(self.path)
