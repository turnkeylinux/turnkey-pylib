import datetime

class DateError(Exception):
    pass
    
def parsedate(datestr):
    """Parse <datestr> > datetime.date() instance
    <datestr> := YY[YY][/MM[/DD]]
    """
    vals = datestr.split("/")
    try:
        if len(vals) == 3:
            year, month, day = map(int, vals)
        elif len(vals) == 2:
            year, month = map(int, vals)
            day = 1
        elif len(vals) == 1:
            year = int(vals[0])
            month = 1
            day = 1
        else:
            raise ValueError()
    except ValueError:
        raise DateError("illegal date (%s)" % datestr)

    if year < 100:
        if year > 70:
            year += 1900
        else:
            year += 2000
        
    return datetime.date(year, month, day)
