"""

Quick reference:

1) Decorator usage:

    @trace(callback=printer)
    @trace()
    @trace

2) Set new default callback:

    def new_callback(s):
        pass

    trace.callback = new_global_callback

    # disable trace function
    trace.callback = None

Long version:

When you want to trace out function foo (print when it is called with
what arguments) you just add the @trace decorator to it.

Like this::

    from debug import trace

    @trace
    def foo(...):
        pass

You can also provide your own printing callback (e.g., to a logfile
instead of stdout) and you can provide it at the decorator level::

    @trace(callback=tomylogfile)
    def foo(...)

Or at the module level::

    from debug import trace

    trace.callback = tomylogfile

    @trace
    def foo(...)

By default @trace prints to stdout but you can disable it::

    trace.callback = None

    @trace
    def foo(...)

This allows you to use the module level callback to implement a global
wide --debug flag. You pepper all the things you want to log / debug
with a trace decorator and only enable the callback if the user sets
--debug.


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
        callable = callback if callback else trace.callback
        if callable:

            s = func.__name__ + "("
            if args:
                s += ", ".join(_fmt(arg, trunc) for arg in args)

            if kwargs:
                s += ", " + ", ".join("%s=%s" % (key, _fmt(val, trunc))
                                        for key,val in kwargs.items())

            s += ")"
            callable(s)

        return func(*args, **kwargs)

    return wrapper
