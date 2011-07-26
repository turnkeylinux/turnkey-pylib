import signal

def sigignore(*sigs):
    def decorate(method):
        def wrapper(*args, **kwargs):
            orig_handlers = []

            for sig in sigs:
                orig_handlers.append(signal.getsignal(sig))
                signal.signal(sig, signal.SIG_IGN)

            try:
                return method(*args, **kwargs)
            finally:

                for (i, sig) in enumerate(sigs):
                    signal.signal(sig, orig_handlers[i])

        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__

        return wrapper
    return decorate


def test():
    import time
    def handler(sig, frame):
        print "caught sig %d" % sig

    signal.signal(signal.SIGINT, handler)
    print "before time.sleep(5) with Ctrl-C ignored"
    sigignore(signal.SIGINT)(time.sleep)(5)
    print "after sleep"

    print "before time.sleep(5)"
    time.sleep(10)
    print "after sleep"

if __name__ == "__main__":
    test()
