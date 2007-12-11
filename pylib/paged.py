"""This modules provides an stdout instances which
redirect output through a pager if:
  A) PAGER is configured in the environment
  B) stdout is not a tty
"""

import os
import sys
import errno

class _PagedStdout:
    # lazy definition of pager attribute so that we
    # execute pager the first time we need it
    def pager(self):
        if hasattr(self, '_pager'):
            return self._pager

        pager = None
        if os.isatty(sys.stdout.fileno()):
            pager_env = os.environ.get('PAGER')
            if pager_env:
                pager = os.popen(pager_env, "w")

        self._pager = pager
        return pager
    pager = property(pager)

    def flush(self):
        if self.pager:
            self.pager.flush()
        else:
            sys.stdout.flush()
        
    def write(self, text):
        if self.pager:
            try:
                self.pager.write(text)
                
            except IOError, e:
                if e[0] != errno.EPIPE:
                    raise
        else:
            sys.stdout.write(text)

stdout = _PagedStdout()

def test():
    print >> stdout, "foo"
    stdout.write("bar")

if __name__=="__main__":
    test()

