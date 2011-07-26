from __future__ import with_statement
import signal

class sigignore:
    def __init__(self, *sigs):
        self.sigs = sigs
        self.orig_handlers = None

    def _ignore(self):
        self.orig_handlers = []
        for sig in self.sigs:
            self.orig_handlers.append(signal.getsignal(sig))
            signal.signal(sig, signal.SIG_IGN)

    def _restore(self):
        for (i, sig) in enumerate(self.sigs):
            signal.signal(sig, self.orig_handlers[i])

        self.orig_handlers = None

    def __call__(self, method):
        def wrapper(*args, **kwargs):

            self._ignore()
            try:
                return method(*args, **kwargs)
            finally:
                self._restore()

        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__

        return wrapper

    def __enter__(self):
        self._ignore()
        return self

    def __exit__(self, type, value, tb):
        self._restore()

def test():
    import time
    def handler(sig, frame):
        print "caught sig %d" % sig

    @sigignore(signal.SIGINT)
    def sleep(seconds):
        time.sleep(seconds)

    signal.signal(signal.SIGINT, handler)

    print "before decorated sleep(3) (ignoring Ctrl-C)"
    sleep(3)
    print "after sleep"

    with sigignore(signal.SIGINT):
        print "inside sigignore with statement, before time.sleep(3)"
        time.sleep(3)
        print "after sleep"

    print "before time.sleep(5)"
    time.sleep(10)
    print "after sleep"

if __name__ == "__main__":
    test()
