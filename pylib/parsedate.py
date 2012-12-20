# Copyright (c) 2007 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import re
import datetime

class DateError(Exception):
    pass

def parsedate(datestr):
    """Supported date formats:
       N days|months|weeks|years ago

       DD/MM[/YY[YY]]
       DD-MM[-YY[YY]]
       DD.MM[.YY[YY]]

       YYYY/MM[/DD]
       YYYY-MM[-DD]
       YYYY.MM[.DD]

       YYYY
    """
    try:
        year = int(datestr)
        if year >= 1000:
            return datetime.date(year, 1, 1)
    except ValueError:
        pass

    m = re.match(r'(\d+)\s+(day|month|week|year)s?\s*(?:ago)?$', datestr)
    if m:
        num = int(m.group(1))
        unit = m.group(2)

        if unit == 'week':
            num *= 7
        elif unit == 'month':
            num *= 30
        elif unit == 'year':
            num *= 365

        days = num
        return datetime.date.today() - datetime.timedelta(days)

    m = re.match(r'(\d\d?)/(\d\d?)(?:/(\d\d\d?\d?))?$', datestr)
    if not m:
        m = re.match(r'(\d\d?)-(\d\d?)(?:-(\d\d\d?\d?))?$', datestr)
        if not m:
            m = re.match(r'(\d\d?)\.(\d\d?)(?:\.(\d\d\d?\d?))?$', datestr)
        
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3) or datetime.date.today().year)
        if year < 100:
            if year > 70:
                year += 1900
            else:
                year += 2000

        return datetime.date(year, month, day)
    

    m = re.match(r'(\d\d\d\d)/(\d\d?)(?:/(\d\d?))?$', datestr)
    if not m:
        m = re.match(r'(\d\d\d\d)-(\d\d?)(?:-(\d\d?))?$', datestr)
        if not m:
            m = re.match(r'(\d\d\d\d)\.(\d\d?)(?:\.(\d\d?))?$', datestr)
            
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        if m.group(3):
            day = int(m.group(3))
        else:
            day = 1
            
        return datetime.date(year, month, day)

    raise DateError("illegal date (%s)" % datestr +
                    "\n" + parsedate.__doc__)


        

