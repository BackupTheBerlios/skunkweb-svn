import sys
import time
import re
import datetime

# try to import 3rd party time modules
try:
    from mx import DateTime
    _have_mx=1
except ImportError:
    _have_mx=0

try:
    import dateutil
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse as _parse_dateutil
    _have_dateutil=1
except ImportError:
    _have_dateutil=0

class TimeException(ValueError):
    pass

class PastTimeException(TimeException):
    pass


_is_mx_DateTime=lambda x: _have_mx and \
                 isinstance(x, DateTime.DateTimeType)
_is_mx_RelativeDateTime=lambda x: _have_mx and \
                         isinstance(x, DateTime.RelativeDateTime)
_is_dateutil_relativedelta=lambda x: _have_dateutil and \
                            isinstance(x, relativedelta)

def _to_ticks(x):
    if x is None:
        return time.time()
    if isinstance(x, int) or isinstance(x, float):
        return x
    if isinstance(x, datetime.datetime):
        return time.mktime(x.timetuple())
    if _is_mx_DateTime(x):
        return x.ticks()
    raise ValueError, "unrecognized type: %s" % x

def convert(thing, curdate=None):
    if isinstance(thing, basestring):
        try:
            return convertDuration(thing, curdate)
        except TimeException:
            pass
    elif isinstance(thing, (list,tuple)):
        try:
            return min(convert(x, curdate) for x in thing)
        except TimeException:
            pass
                    
    return convertUntil(thing, curdate)

def convertDuration(duration, curdate=None):
    """
    >>> import time; t=time.time()
    >>> convertDuration("1h", t)==t+3600
    True
    """
    return timeConv(duration) + _to_ticks(curdate)

def convertUntil(until, curdate=None):
    curdate=_to_ticks(curdate)

    if isinstance(until, (int, long, float)):
        return until
    
    if isinstance(until, basestring):
	result = _untilString(until, curdate)    
        
    ## if until is a DateTime object, consider it to be in local server
    ## time, and return the ticks.
        
    elif _is_mx_DateTime(until):
        result = until.ticks()
        
    ##  elif a RelativeDateTime, add it to the current date
    elif _is_mx_RelativeDateTime(until):
	result = (DateTime.DateTimeFromTicks(curdate)+until).ticks()

    ## elif a dateutil relativedelta, add to current date
    elif _is_dateutil_relativedelta(until):
        t=until+datetime.datetime.fromtimestamp(curdate)
        result = time.mktime(t.timetuple())
        
    ## elif a list or tuple of items, run convertUntil on each, take
    ## the minimum value in the result list, and return that.
    elif isinstance(until, list) or isinstance(until, tuple):
	lowres = None
	for i in until:
	    thisone = convertUntil(i, curdate)
	    if lowres is None or thisone < lowres:
		lowres = thisone
        result = lowres

    else:
        raise TimeException, \
              "unsupported type: %s (%s)" % (type(until), until)

    if result < curdate:
        raise PastTimeException, until
    return result

# helper re's for _untilString
_min_after_hour = re.compile(r'^:\d{2}$')
_timespec       = re.compile(r'^\d{2}:\d{2}(:\d{2})?$')
_datespec  = re.compile(r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$')

_digits = '0123456789'


def _until_timespec(curticks, hr, min, sec):
    """
    >>> t=time.strptime('200212312359', '%Y%m%d%H%M')
    >>> u=_until_timespec(time.mktime(t), 4, 20, 32)
    >>> time.ctime(u)
    'Wed Jan  1 04:20:32 2003'
    """    
    ttuple=time.localtime(curticks)
    ntuple=ttuple[:3] + (hr, min, sec) + ttuple[-3:]
    nt=time.mktime(ntuple)
    if nt > curticks:
        return nt
    else:
        # add a day, but the length of the day
        # depends on whether we are on the cusp
        # of a change in DST status.  
        dst1=ntuple[-1]
        # 24 hours later
        nextday=nt+86400
        nexttuple=time.localtime(nextday)
        dst2=nexttuple[-1]
        if dst1==dst2:
            # no change in dst
            return nextday
        elif dst1<dst2:
            # 23 hours
            return nt+82800
        else:
            # 25 hours
            return nt+90000
            
def _untilString(until, curdate=None):
    """\
    handles all cases where until argument is a string
    """
    curdate=_to_ticks(curdate)

    # if it looks like a "minutes after hour", return current date
    # rounded up to the next minute
    if until[0]== ':' and until[1] in _digits and until[2] in _digits:
	mins = int(until[1:])
        # we may need to roll over the hour, and I want to avoid using
        # mx or dateutil, hence the following arithmetic.  Leap
        # seconds be damned.
        curmin=time.localtime(curdate)[4]
        secs_to_add=((mins-curmin) % 60)* 60
        return curdate+secs_to_add
    
    # elif it looks like just a timespec, return current date with
    # time set to that.
    elif _timespec.search(until):
	parts = until.split(':')
	if len(parts) == 2:
            parts.append('00')
	hr, min, sec = map(int, parts)
        return _until_timespec(curdate, hr, min, sec)

    # elif it looks like a datespec, make a date.
    elif _datespec.search(until):
        return _parse_ISO(until)
    else:
        raise TimeException, until

def timeConv(s):
    """convert a time like 9d20h10m15s to seconds"""
    tot=0
    lastind=0
    for i in range(len(s)):
        c=s[i]
        if c=='d':
            tot=tot+int(s[lastind:i])*86400
            lastind=i+1
        elif c=='h':
            tot=tot+int(s[lastind:i])*3600
            lastind=i+1
        elif c=='m':
            tot=tot+int(s[lastind:i])*60
            lastind=i+1
        elif c=='s':
            tot=tot+int(s[lastind:i])
            lastind=i+1
        elif c not in _digits:
            raise TimeException, s
    return tot 

def _parse_ISO(datestr):
    """
    >>> _parse_ISO('2003-10-21 15:30')
    1066764600.0
    >>> _parse_ISO('2003-10-21')
    1066708800.0
    """
    formats=['%Y-%m-%d %H:%M:%S',
             '%Y-%m-%d %H:%M',
             '%Y-%m-%d',
             '%Y-%m']
    for f in formats:
        try:
            return time.mktime(time.strptime(datestr, f))
        except ValueError:
            continue
    raise TimeException, datestr
             

__all__=['convert']

if __name__=='__main__':
    import doctest, timeutil
    doctest.testmod(timeutil)
