# Copyright (c) 2007 Liraz Siri <liraz@sterilesecurity.com> - all rights reserved
import fcntl

class Lock:
    class Error(Exception):
        pass
    
    def __init__(self, filename, nonblock=False):
        self.filename = filename
        self.nonblock = nonblock
        self.locked = False

    def lock(self, nonblock=None):
        self.fh = file(self.filename, "w+")

        if nonblock is None:
            nonblock = self.nonblock 
        
        flags = 0
        if nonblock:
            flags = fcntl.LOCK_NB
        try:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | flags)
        except IOError:
            raise self.Error("locked: " + self.filename)

        self.locked = True

    def unlock(self):
        fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        self.fh = None

        self.locked = False

# run this twice for best effect
def _test():
    import time
    
    def sleep(n):
        print "sleeping for %d seconds" % n
        time.sleep(n)

    l = Lock("lock.lock", nonblock=False)
    l.lock()
    sleep(5)
    l.unlock()

    sleep(0.1)

    l.lock()
    sleep(5)
    l.unlock()

if __name__ == '__main__':
    _test()
