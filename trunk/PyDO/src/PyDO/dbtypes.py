import datetime
import time
try:
    import mx.DateTime
    havemx=True
except ImportError:
    havemx=False

class typewrapper(object):
    __slots__=('value',)
    def __init__(self, value):
        self.value=value

class DATE(typewrapper):
    def __init__(self, *value):
        lenval=len(value)
        if lenval==0:
            # current date
            self.value=datetime.date.today()[:3]
        elif lenval==1:
            value=value[0]
            if isinstance(value, (long, int, float)):
                self.value=time.localtime(value)[:3]
            elif isinstance(value, (datetime.date, datetime.datetime)):
                self.value=value.timetuple()[:3]
            elif havemx and isinstance(value, mx.DateTime):
                self.value=(value.year, value.month, value.day)
            elif isinstance(value, basestring):
                self.value=time.strptime('%m-%d-%Y', value)[:3]
        elif lenval==3:
            self.value=value
        else:
            raise ValueError, "can't coerce to a date"


class TIMESTAMP(typewrapper):
    pass

class INTERVAL(typewrapper):
    pass

class BINARY(typewrapper):
    pass

__all__=['DATE', 'TIMESTAMP', 'INTERVAL', 'BINARY']    
