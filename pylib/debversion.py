# Copyright (c) 2007 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import re
import string

def parse(v):
    if ':' in v:
        epoch, v = v.split(':', 1)
    else:
        epoch = '0'

    if '-' in v:
        upstream_version, debian_revision = v.rsplit('-', 1)
    else:
        upstream_version = v
        debian_revision = '0'

    return epoch, upstream_version, debian_revision

class VersionParser:
    def __init__(self, str):
        self.str = str

    def getlex(self):
        str = self.str
        i = 0
        for c in str:
            if c in '0123456789':
                break
            i += 1

        if i:
            lex = str[:i]
            self.str = str[i:]

            return lex

        return ''

    def getnum(self):
        str = self.str
        i = 0
        for c in str:
            if c not in '0123456789':
                break
            i += 1

        if i:
            num = int(str[:i])
            self.str = str[i:]

            return num

        return 0

def _lexcmp(a, b):
    i = 0
    while True:
        if i < len(a) and a[i] == '~' and (i >= len(b) or b[i] != '~'):
            return -1

        if i < len(b) and b[i] == '~' and (i >= len(a) or a[i] != '~'):
            return 1

        if len(a) == len(b):
            if i == len(a):
                return 0
        else:
            if i == len(a):
                return -1

            if i == len(b):
                return 1

        if a[i].isalpha():
            if not b[i].isalpha():
                return -1

        if b[i].isalpha():
            if not a[i].isalpha():
                return 1

        val = cmp(a[i], b[i])
        if val != 0:
            return val

        i += 1

# _compare is functionally equivalent to _compare_flat
# only its much more readable
def _compare(s1, s2):
    if s1 == s2:
        return 0

    p1 = VersionParser(s1)
    p2 = VersionParser(s2)

    while True:
        l1 = p1.getlex()
        l2 = p2.getlex()

        val = _lexcmp(l1, l2)
        if val != 0:
            return val

        n1 = p1.getnum()
        n2 = p2.getnum()
        
        val = cmp(n1, n2)
        if val != 0:
            return val

        if p1.str == p2.str:
            return 0

# _compare_flat is functionally equivalent to _compare
# but it embeds VersionParser's functionality inline for optimization
def _compare_flat(s1, s2):
    if s1 == s2:
        return 0

    while True:
        # parse lexical components
        i = 0
        for c in s1:
            if c in '0123456789':
                break
            i += 1

        if i:
            l1 = s1[:i]
            s1 = s1[i:]
        else:
            l1 = ''

        i = 0
        for c in s2:
            if c in '0123456789':
                break
            i += 1

        if i:
            l2 = s2[:i]
            s2 = s2[i:]
        else:
            l2 = ''

        val = _lexcmp(l1, l2)
        if val != 0:
            return val

        # if lexical component is equal parse numeric component
        i = 0
        for c in s1:
            if c not in '0123456789':
                break
            i += 1

        if i:
            n1 = int(s1[:i])
            s1 = s1[i:]

        else:
            n1 = 0

        i = 0
        for c in s2:
            if c not in '0123456789':
                break
            i += 1

        if i:
            n2 = int(s2[:i])
            s2 = s2[i:]

        else:
            n2 = 0

        val = cmp(n1, n2)
        if val != 0:
            return val

        if s1 == s2:
            return 0

def compare(a, b):
    """Compare a with b according to Debian versioning criteria"""

    a = parse(a)
    b = parse(b)

    for i in (0, 1, 2):
        val = _compare_flat(a[i], b[i])
        if val != 0:
            return val

    return 0

def test():
    try:
       import psyco; psyco.full()
    except ImportError:
       pass
    
    import time
    howmany = 10000
    start = time.time()
    for i in xrange(howmany):
        compare("0-2007.10.1-d6cbb928", "0-2007.10.10-a9ee521c")
    end = time.time()
    elapsed = end - start

    print "%d runs in %.4f seconds (%.2f per/sec)" % (howmany, elapsed,
                                                      howmany / elapsed)

if __name__ == "__main__":
    test()
