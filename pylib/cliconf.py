"""Pythonic cli configuration module

Features:

- Elegant Pythonic interface
- Accept configuration from hierarchy of sources:

    1) command line (highest precedence)
    2) environment variable
    3) configuration file (test.conf)
    4) built-in default (lowest precedence)

- Automatic formatting of embedded usage information

Example usage::

    from cliconf import *
    class MyOpts(Opts):

        myopt = Opt(short="o")
        mybool = BoolOpt(short="b")

        simple_opt = ""
        simple_bool = False

    class MyCliConf(CliConf):
        "Syntax: $AV0 [-options] <arg>"

        Opts = MyOpts

        # if you don't configure env_path
        # the environment doesn't configure options

        env_path = "MYPROG_" 

        # if you don't configure file_path
        # no configuration file is supported

        file_path = "/etc/myprog.conf"

    try:
        opts, args = MyCliConf.getopt()
    except MyCliConf.Error, e:
        MyCliConf.usage(e)

    if not args:
        MyCliConf.usage("not enough arguments")

    for opt in opts:
        print "%s=%s" % (opt.name, opt.val)
        print `dict(opt)`
"""

import os
import sys
import getopt
import copy
import types
import re
import string

class Opt(object):
    """This class represents an option.
    
    Iterator allows us to convert instance into a mapping/dictionary 

    Example usage::

        print opt.name
        print `dict(opt)`

    """

    def __init__(self, desc=None, short="", protect=False, default=None):
        """Arguments:
           <desc>       description of option (I.e., for usage)
           <short>      one letter flag
           <protect>    True if option is protected in suid mode
           <default>    Default value
        """

        self.desc = desc
        self.short = short
        self.protect = protect

        self.val = default
        self.name = None

    def __iter__(self):
        for attrname, attr in vars(self).items():
            yield attrname, attr

    def longopt(self):
        if self.name:
            return self.name.replace("_", "-")

        return ""
    longopt = property(longopt)

    def protected(self):
        # protected options can't be set in suid mode
        if self.protect and os.getuid() != os.geteuid():
            return True

        return False
    protected = property(protected)

class BoolOpt(Opt):
    """This class represents a boolean option"""
    @staticmethod
    def parse_bool(val):
        if val.lower() in ('', '0', 'no', 'false'):
            return False

        if val.lower() in ('1', 'yes', 'true'):
            return True

        raise Error("illegal value for bool (%s)" % val)

    def set_val(self, val):
        if val not in (None, True, False):
            val = self.parse_bool(str(val))
            
        self._val = val

    def get_val(self):
        if hasattr(self, '_val'):
            return self._val

        return None

    val = property(get_val, set_val)

def is_bool(opt):
    return isinstance(opt, BoolOpt)

class Opts:
    """This class represents a collection of options.

    The user configures a set of options by inheriting from this class
    and setting class attributes which represent individual options.

    Options can be specified in full form, as instances of Opt or
    subclass, or in simple form as a built-in Python value which is
    converted into an Opt value when Opts is initialized by CliConf::

        class MyOpts(Opts):

            myopt = Opt(short="o")
            mybool = BoolOpt(short="b")

            simple_opt = ""
            simple_bool = False

    This configured class can specify which options will be parsed by CliConf::

        class MyCliConf(CliConf):
            Opt = MyOpt

    CliConf.getopt() returns an instance of this class that can be
    accessed to query the states of various options.

    Instances of this class implement a bit of magic to allow the
    class to have a more natural Pythonic interface.

        1) Object interface::

            opt = opts.my_opt
            print opt.name

        2) Sequence-like interface::

            for opt in opts:
                print opt.name

        3) Dictionary-like interface::

            if 'my_opt' in opts:
                print opts['my_opt'].name

    """
    def __init__(self):
        # make copies of options
        for attrname, attr in vars(self.__class__).items():
            if attrname[0] == "_":
                continue

            if isinstance(attr, Opt):
                attr = copy.copy(attr)
            elif isinstance(attr, types.BooleanType):
                attr = BoolOpt(default=attr)
            else:
                attr = Opt(default=attr)

            attr.name = attrname
            setattr(self, attrname, attr)

    def __iter__(self):
        for attr in vars(self).values():
            if isinstance(attr, Opt):
                yield attr

    def __getitem__(self, attrname):
        attr = getattr(self, attrname)
        if isinstance(attr, Opt):
            return attr

        raise KeyError(`attrname`)

    def __contains__(self, opt):
        if isinstance(opt, Opt):
            return opt in list(self)

        if isinstance(opt, types.StringType):
            attr = getattr(self, opt, None)
            if isinstance(attr, Opt):
                return True
            return False

        raise TypeError("type(%s) not a string or an Opt instance" %
                        `opt`)

class Error(Exception):
    pass

class CliConf:
    """Cli configuration class.
    
    This class is configured via inheritance::
    
        class MyCliConf(CliConf):
            "Syntax: $AV0 [-options] <arg>"

            Opts = MyOpts

    All methods in this class are either static methods or class
    methods, so creating an instance of this class before use is not
    required::

        try:
            opts, args = MyCliConf.getopt()
        except MyCliConf.Error, e:
            MyCliConf.usage(e)

    """
    Error = Error

    env_path = None
    file_path = None

    @classmethod
    def _cli_getopt(cls, args, opts):
        # make arguments for getopt.gnu_getopt
        longopts = ['help']
        shortopts = "h"

        for opt in opts:
            longopt = opt.longopt
            shortopt = opt.short

            if not is_bool(opt):
                longopt += "="

                if shortopt:
                    shortopt += ":"

            longopts.append(longopt)
            shortopts += shortopt

        try:
            opts, args = getopt.gnu_getopt(args, shortopts, longopts)
        except getopt.GetoptError, e:
            raise Error(e)

        for opt, val in opts:
            if opt in ('-h', '--help'):
                cls.usage()

        return opts, args

    @staticmethod
    def _parse_conf_file(path):
        try:
            fh = file(path)

            for line in fh.readlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                name, val = re.split(r'\s+', line)
                yield name, val
        except IOError:
            pass
    
    @classmethod
    def getopt(cls, args=None):
        opts = cls.Opts()

        if cls.file_path:
            for name, val in cls._parse_conf_file(cls.file_path):
                name = name.replace("-", "_")

                if name not in opts:
                    raise Error("unknown configuration file option `%s'" %
                                name)

                opts[name].val = val

        # set options that are set in the environment
        if cls.env_path is not None:
            for opt in opts:
                optenv = cls.env_path + opt.name
                optenv = optenv.upper()

                if optenv not in os.environ:
                    continue

                if opt.protected:
                    continue
                
                opt.val = os.environ[optenv]

        if not args:
            args = sys.argv[1:]
                
        cli_opts, args = cls._cli_getopt(args, opts)
        for cli_opt, cli_val in cli_opts:
            for opt in opts:
                if cli_opt in ("--" + opt.longopt,
                               "-" + opt.short):

                    if opt.protected:
                        raise Error("protected option (%s) can't be set while running suid" % opt.name)

                    if is_bool(opt):
                        opt.val = True
                    else:
                        opt.val = cli_val

        return opts, args

    @classmethod
    def usage(cls, err=None):
        if err:
            print >> sys.stderr, "error: " + str(err)

        if cls.__doc__:
            tpl = string.Template(cls.__doc__)
            buf = tpl.substitute(AV0=os.path.basename(sys.argv[0]))
            print >> sys.stderr, buf.strip()

        order = ['command line (highest precedence)']
        if cls.env_path:
            order.append('environment variable')

        if cls.file_path:
            order.append('configuration file (%s)' % cls.file_path)

        order.append('built-in default (lowest precedence)')

        buf = "\n"
        buf += "Resolution order for options:\n"

        for i in range(1, len(order) + 1):
            buf += "%d) %s\n" % (i, order[i - 1])

        print >> sys.stderr, buf

        opts = cls.Opts()
        rows = []
        for opt in opts:
            col1 = ""
            if opt.short:
                col1 += "-%s " % opt.short

            col1 += "--" + opt.longopt
            if not is_bool(opt):
                col1 += "="

            col2 = []
            if opt.desc:
                col2.append(opt.desc)

            if cls.env_path:
                optenv = cls.env_path + opt.name
                col2.append("environment: " + optenv.upper())

            if opt.val is not None:
                col2.append("default: " + str(opt.val))

            rows.append((opt, col1, col2))

        print >> sys.stderr, "Options: "
        col1_maxlen = max([ len(col1) for opt, col1, col2 in rows ]) + 2

        def format_option(col1, col2):
            padding = " " * (col1_maxlen - len(col1))
            line = "  " + col1 + padding
            if col2:
                line += col2[0]
                del col2[0]

            buf = line + "\n"
            for col in col2:
                buf += "  " + " " * col1_maxlen + col + "\n"

            return buf

        protected_rows = [ (col1, col2) for opt, col1, col2 in rows if opt.protected ]
        rows = [ (col1, col2) for opt, col1, col2 in rows if not opt.protected ]

        for col1, col2 in rows:
            print >> sys.stderr, format_option(col1, col2)

        if protected_rows:
            print >> sys.stderr, "\nProtected options (root only):\n"
            for col1, col2 in protected_rows: 
                print >> sys.stderr, format_option(col1, col2)

        if cls.file_path:
            buf = "Configuration file format (%s):\n\n" % cls.file_path
            buf += "  <option-name> <value>\n\n"

            print >> sys.stderr, buf,

        sys.exit(1)

def test():
    class TestOpts(Opts):
        bool = BoolOpt("a boolean flag", short="b", default=False)
        val = Opt("a value", short="v")
        a_b = Opt()

        simple = "test"
        simplebool = False

    class TestCliConf(CliConf):
        """Syntax: $AV0 [-options] <arg>
        """

        Opts = TestOpts

        env_path = "TEST_"
        file_path = "test.conf"

    import pprint
    pp = pprint.PrettyPrinter()

    try:
        opts, args = TestCliConf.getopt()
    except TestCliConf.Error, e:
        TestCliConf.usage(e)

    if len(args) != 1:
        TestCliConf.usage("not enough arguments")

    print "--- OPTIONS:"
    pp.pprint([ dict(opt) for opt in opts])
    for opt in opts:
        print "%s=%s" % (opt.name, opt.val)

    arg = args[0]
    print "arg = " + `arg`

if __name__ == "__main__":
    test()

