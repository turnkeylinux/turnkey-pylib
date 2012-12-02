class State:
    """
    Base class for object that knows how to save itself.

    s = State()
    s.pid = 123
    text = s.freeze()

    copy_s = State()
    copy_s.thaw(text)
    
    """
    class Error(Exception):
        pass
    
    from ConfigParser import ConfigParser
    from cStringIO import StringIO

    SECTION_NAME="state"

    def freeze(self):
        """
        Serialize the state object into a string
        """
        parser = self.ConfigParser()
        parser.add_section(self.SECTION_NAME)
        for attr in self.__dict__.keys():
            parser.set(self.SECTION_NAME, attr, getattr(self, attr))

        fh = self.StringIO()
        parser.write(fh)
        return fh.getvalue()

    def thaw(self, serialized):
        """
        Thaw the state object from a string
        """
        parser = self.ConfigParser()
        parser.readfp(self.StringIO(serialized))
        if not parser.has_section(self.SECTION_NAME):
            raise self.Error("bad serialized state, missing section '%s'" % self.SECTION_NAME)
        for attr in self.__dict__.keys():
            if not parser.has_option(self.SECTION_NAME, attr):
                raise self.Error("bad serialized state, missing attribute '%s'" % attr)

            attr_type = type(getattr(self, attr))
            setattr(self, attr, attr_type(parser.get(self.SECTION_NAME, attr)))
    
class StateFile(State):
    """
    Base class for an object that maintains its state in a file.

    Loads attributes from a file on thaw()
    Saves all of it's attributes to a file on freeze()
    """

    STATE_FILE = "/path/to/state"
    
    def freeze(self):
        serialized = State.freeze(self)
        file(self.STATE_FILE, "w").write(serialized)

    def thaw(self):
        serialized = file(self.STATE_FILE, "r").read()
        State.thaw(self, serialized)
