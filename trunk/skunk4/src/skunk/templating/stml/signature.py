from skunk.templating.stml.exceptions import SignatureError

def find_duplicates(arglist):
    d={}
    e={}
    for a in arglist:
        if d.has_key(a):
            e[a]=1
        else:
            d[a]=1
    return e.keys()

class Signature(object):
    """
    A representation of an STML tag signature,
    which is in fact just like a Python method
    signature.  The constructor takes 3 arguments:
    
      1. a sequence of argument names and argument name/default value
         pairs, with the constraint, as with Python, that bare
         argument names must precede those with defaults;
      2. the variable name of excess positional arguments, if allowed;
      3. the variable name of excess keyword arguments, if allowed.
    
    The resolve_arguments() method is passed a sequence of positional
    arguments and a dictionary of keyword arguments, returns a
    dictionary of those values that would be available in a Python
    method with that stated signature called with those values.

    Example usage:
        
    >>> s=Signature(('x', 'y', ('z', 100)), None, 'kwargs')
    >>> s.resolve_arguments((30, 20), {'a' : -4})
    {'x' : 30, 'y' : 20, 'z' : 100, 'kwargs' : {'a' : -4}}

    The class features somewhat robust input validation, and will
    raise a SignatureError for invalid signatures, and ValueError if
    you are being particularly silly.
    """
    __slots__=['args',
               'excess_positional_args',
               'excess_keyword_args']
    
    def __init__(self,
                 args=(),
                 excess_positional_args=None,
                 excess_keyword_args=None):

        # check input        
        found_k=False
        for a in args:
            if isinstance(a, tuple):
                if len(a)!=2:
                    raise ValueError, \
                          "invalid signature: tuple args must be of length 2"
                found_k=True
            else:
                if found_k:
                    raise ValueError, \
                          "invalid signature: positional argument after keyword argument"

        # check for duplicates
        dups=find_duplicates(filter(None,
                                    [x[0] for x in args if isinstance(x, tuple)]+\
                                    [excess_positional_args,
                                     excess_keyword_args]))
        if dups:
            raise SignatureError, "duplicate argument names in signature: %s" % ", ".join(dups)
                
        # args ok, proceed        
        self.args=args                
        self.excess_positional_args=excess_positional_args
        self.excess_keyword_args=excess_keyword_args
        
    def resolve_arguments(self, positional_args, keyword_args):
        arg_slots={}
        # a separately maintained list of what slots are available
        available=[]
        defaults=dict([x for x in self.args if isinstance(x, tuple)])

        for a in self.args:
            if isinstance(a, tuple):
                available.append(a[0])
            else:
                available.append(a)

        extrapos=[]
        extrakeys={}
        if self.excess_positional_args:
            arg_slots[self.excess_positional_args]=extrapos
        if self.excess_keyword_args:
            arg_slots[self.excess_keyword_args]=extrakeys
            
        for i, p in enumerate(positional_args):
            try:
                k=self.args[i]
            except IndexError:
                if self.excess_positional_args:
                    extrapos.append(p)
                else:
                    raise SignatureError, "extra positional arg: %s" % str(p)
            else:
                if isinstance(k, tuple):
                    k=k[0]
                arg_slots[k]=p
                available.remove(k)

                
                
        for k, v in keyword_args.iteritems():
            if k in available:
                arg_slots[k]=v
                available.remove(k)
            elif k in arg_slots:
                raise SignatureError, "two arguments provided with same name: %s" % k
            elif self.excess_keyword_args:
                if extrakeys.has_key(k):
                    raise SignatureError, "two arguments provided with same name: %s" % k
                else:
                    extrakeys[k]=v
            else:
                raise SignatureError, "unexpected keyword argument: %s" % k

        for k in defaults:
            if k not in arg_slots:
                arg_slots[k]=defaults[k]
                available.remove(k)

        if available:
            raise SignatureError, "not all required arguments provided: %s" % \
                  ", ".join(map(str, available))
            
        return arg_slots


__all__=['Signature']            
