class SuperDict(dict):
    """
    Usage:

        class Foo(SuperDict):
            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

        foo = Foo(1, 2, 3)
        assert foo['a'] == foo.a

    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)

    def __setattr__(self, name, val):
        self[name] = val

