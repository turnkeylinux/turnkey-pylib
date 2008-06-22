"""This module implement lazy object construction.

Usage:

    class A:
        def __init__(self, a):
            print "A(%s)" % a
            self.a = a

    # initialized immediately
    a = A(111)
    print a.a

    LazyA = lazyclass(A)

    # not really initialized yet
    a = LazyA(111)

    # initialized now (first attribute access)
    print a.a

"""

class LazyClassWrapper(object):
    __local_attr__ = ['_init_args', '_object_val']

    def __init__(self, constructor, *args, **kws):
        self._init_args = (constructor, args, kws)
        self._object_val = None

    def _eval_object(self):
        if self._object_val:
            return self._object_val

        constructor, args, kws = self._init_args
        self._object_val = constructor(*args, **kws)

        return self._object_val

    _object = property(_eval_object)

    def __setattr__(self, attrname, val):
        if attrname in self.__local_attr__:
            return object.__setattr__(self, attrname, val)

        setattr(self._object, attrname, val)

    def __getattr__(self, attrname):
        return getattr(self._object, attrname)

    def __str__(self):
        return str(self._object)

    def __repr__(self):
        return repr(self._object)

def lazyclass(constructor):
    def wrapper(*args, **kws):
        return LazyClassWrapper(constructor, *args, **kws)
    return wrapper

def test():
    class Name:
        def __init__(self, name):
            self.name = name

            print "initializing Name(%s)" % name

        def val(self):
            return self.name

        def __str__(self):
            return "name=" + self.name

    LazyName = lazyclass(Name)

    print "before regular initialization"
    n = Name("notlazy")
    print "after regular initialization"

    print "n.name = " + n.name

    print "----------"

    print "before lazy initialization"
    ln = LazyName("lazy")
    print "after lazy initialization"

    print "ln.name = " + ln.name

    return ln

if __name__ == "__main__":
    test()
