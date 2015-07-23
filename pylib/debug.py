"""
Decorator usage:

    @trace(callback=printer)
    @trace()
    @trace

Set new default callback:

    def new_callback(s):
        pass

    trace.callback = new_callback

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

def trace(*args, **kwargs):
    if args and isinstance(args[0], types.FunctionType):
        return _trace(args[0])

    def decorator(func):
        return _trace(func, *args, **kwargs)

    return decorator

def _default_callback(s):
    print "TRACE %d: %s" % (os.getpid(), s)

trace.callback = _default_callback

def _trace(func, callback=None, trunc=48):
    def wrapper(*args, **kwargs):
        s = func.__name__ + "("

        if args:
            s += ", ".join(_fmt(arg, trunc) for arg in args)

        if kwargs:
            s += ", " + ", ".join("%s=%s" % (key, _fmt(val, trunc))
                                       for key,val in kwargs.items())

        s += ")"

        if callback:
            callback(s)
        else:
            trace.callback(s)

        return func(*args, **kwargs)

    return wrapper
