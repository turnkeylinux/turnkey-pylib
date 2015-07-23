"""
Usage:

    @trace(callback=printer)
    @trace()
    @trace

"""
import types
import os

def _fmt(val, trunc):
    r = `val`
    if len(r) > trunc:
        end = r[-1]

        r = r[:trunc - 3] + "..."
        if not end.isalnum():
            r += end

    return r

def _trace(func, callback=None, trunc=48):
    def wrapper(*args, **kwargs):
        trace = func.__name__ + "("

        if args:
            trace += ", ".join(_fmt(arg, trunc) for arg in args)

        if kwargs:
            trace += ", " + ", ".join("%s=%s" % (key, _fmt(val, trunc))
                                       for key,val in kwargs.items())

        trace += ")"

        if callback:
            callback(trace)
        else:
            print "TRACE %d: %s" % (os.getpid(), trace)

        return func(*args, **kwargs)

    return wrapper

def trace(*args, **kwargs):
    if args and isinstance(args[0], types.FunctionType):
        return _trace(args[0])

    def decorator(func):
        return _trace(func, *args, **kwargs)

    return decorator
