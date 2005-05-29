"""
utility functions imported by other PyDO modules.
"""

def _tupleize(item):
    """ turns an atom into a tuple with one element,
    and a non-atom into a tuple"""
    if isinstance(item, tuple):
        return item
    if isinstance(item, (set, frozenset, list)):
        return tuple(item)
    return (item,)

def _setize(item):
    """ turns an atom into a frozenset with one element,
    and a non-atom into a frozenset"""
    if isinstance(item, frozenset):
        return item
    if isinstance(item, (tuple, set, list)):
        return frozenset(item)
    return frozenset((item,))


def _strip_tablename(colname):
    i=colname.rfind('.')
    if i==-1:
        return colname
    return colname[i+1:]

def _import_a_class(fqcn):
    lastDot=fqcn.rfind('.')   
    if lastDot==0:
        raise ValueError, "unable to import %s" %fqcn
    if lastDot>0:
        modName=fqcn[:lastDot]
        className=fqcn[lastDot+1:]
        try:
            module=__import__(modName, globals(), locals(), [className])
            return getattr(module, className)
        except (ImportError, AttributeError):
            raise ValueError, "impossible to import: %s" % fqcn
    else:
        raise ValueError, "impossible to import: %s" % fqcn

    
def every(val, iter):
    for i in iter:
        if i != val:
            return False
    return True

def any(val, iter):
    for i in iter:
        if i==val:
            return True
    return False

def iflatten(*l):
    for i in l:
        if isinstance(i, (list, tuple)):
            for i2 in flatten(*i):
                yield i2
        else:
            yield i

def flatten(*l):
    return list(iflatten(*l))

def formatTexp(o, a):
    if o.getTable()==a:
        return a
    return '%s %s' % (o.getTable(), a)

