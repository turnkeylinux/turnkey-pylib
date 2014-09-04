import re
import os
import sys
from distutils.core import setup as _setup

from executil import getoutput, ExecError
from os.path import *

class SetupBase:
    @classmethod
    def setup(cls, **kwargs):
        packages = cls.get_packages()
        if packages:
            kwargs.update(packages=packages)
        _setup(**kwargs)

    @staticmethod
    def get_packages():
        packages = []
        source_path = abspath(dirname(sys.argv[0]))
        for fname in os.listdir(source_path):
            fpath = join(source_path, fname)
            if isdir(fpath) and exists(join(fpath, '__init__.py')):
                packages.append(fname)

        return packages

class Setup(SetupBase):
    @classmethod
    def setup(cls, **kwargs):
        def parse_control(control):
            """parse control fields -> dict"""
            d = {}
            for line in control.split("\n"):
                if not line or line[0] == " ":
                    continue
                line = line.strip()
                i = line.index(':')
                key = line[:i]
                val = line[i + 2:]
                d[key] = val

            return d
        control_fields = parse_control(file("debian/control").read())

        def parse_email(email):
            m = re.match(r'(.*)\s*<(.*)>', email.strip())
            if m:
                name, address = m.groups()
            else:
                name = ""
                address = email

            return name.strip(), address.strip()

        maintainer = control_fields['Maintainer']
        maintainer_name, maintainer_email = parse_email(maintainer)

        d = {
            'name': control_fields['Source'],
            'version': cls.get_version(),
            'description': control_fields['Description'],
            'maintainer': maintainer_name,
            'maintainer_email': maintainer_email
        }
        d.update(kwargs)
        SetupBase.setup(**d)

    @staticmethod
    def get_version():
        try:
            if not exists("debian/changelog"):
                return getoutput("autoversion HEAD")

            output = getoutput("dpkg-parsechangelog")
            version = [ line.split(" ")[1]
                        for line in output.split("\n")
                        if line.startswith("Version:") ][0]
            return version

        except ExecError:
            return None

setup = Setup.setup
