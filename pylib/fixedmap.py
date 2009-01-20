class FixedMap(dict):
    """
    Fixed map class.

    Features:

    * fields are pre-defined in FIELDS class member
    * fields can be accessed as attributed
    * arbitrary fields and attributed can not be set
    * order of items(), keys(), etc. is in the same order as FIELDS

    Limitation:

    * introspection doesn't work like you might expect

    Usage:

        class Foo(FixedMap):
            FIELDS = ['name', 'age']

        foo = Foo('liraz', age=28)
        assert foo['name'] == foo.name

    """
    class Error(Exception):
        pass

    FIELDS = []

    def __init__(self, *args, **kws):
        fields = self.FIELDS

        if len(args) > len(fields):
            raise self.Error("more values (%s) than fields (%s)" % (`args`,
                                                                    `fields`))

        for i in range(len(args)):
            self[fields[i]] = args[i]

        for key in kws:
            if key in self:
                raise self.Error("field '%s' already set" % key)

            self[key] = kws[key]

        for field in fields:
            if field not in self:
                raise self.Error("field '%s' not set" % field)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)

    def __setattr__(self, name, val):
        self[name] = val

    def __setitem__(self, key, val):
        if key not in self.FIELDS:
            raise self.Error("no such field '%s'" % key)

        dict.__setitem__(self, key, val)

    def __iter__(self):
        for field in self.FIELDS:
            yield field

    def keys(self):
        return list(self)

    iterkeys = __iter__

    def items(self):
        items = []
        for key in self:
            items.append((key, self[key]))

        return items
