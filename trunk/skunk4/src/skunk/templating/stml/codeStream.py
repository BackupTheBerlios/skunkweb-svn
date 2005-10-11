from cStringIO import StringIO

class PythonCodeOutputStream(object):
    """
    an output stream with indent() and dedent() methods that cause
    lines to be indented and dedented depending on the state of the
    stream.  The number of tabs can be accessed or directly changed in
    self.indent_level.  Normally, you can ignore absolute indentation
    level and use indent() and dedent() to increase or decrease the
    indentation level by one tab.

    The stream uses spaces (4 by default, but this can be changed with
    the "tabsize" constructor parameter), not tabs, to indent.

    Example use:

    >>> out=PythonCodeOutputStream()
    >>> out.writeln('if 1==0:')
    >>> out.indent()
    >>> out.writeln('print "ahoy there"')
    >>> out.dedent()
    >>> out.writeln('x=3')
    >>> print out.getvalue()
    if 1==0:
        print "ahoy there"
    x=3
    
    """
    def __init__(self,
                 outputStream=None,
                 tabsize=4):
        if outputStream is None:
            self.outputStream=StringIO()
        else:
            self.outputStream=outputStream
        self.indent_level=0
        self.tabsize=tabsize
        self._needindent=True

    def indent(self, tabs=1):
        """
        increment the indent level
        """
        self.indent_level+=tabs

    def dedent(self, tabs=1):
        """
        decrement the indent level
        """
        self.indent_level-=tabs

    def write(self, s):
        """
        writes to the stream,
        indenting if the last write
        ended with a newline
        """
        if self._needindent:
            self.outputStream.write('%s%s' % (' '*(self.indent_level*self.tabsize), s))
        else:
            self.outputStream.write(s)
        if s.endswith('\n'):
            self._needindent=True
        else:
            self._needindent=False

    def writeln(self, s):
        """
        writes a line, adding a line return
        """
        self.write(s+'\n')

    def tell(self):
        return self.outputStream.tell()

    def getvalue(self):
        """
        if the outputStream you are using doesn't
        have this method, don't call it!
        """
        return self.outputStream.getvalue()

    def truncate(self):
        """
        truncate the underlying stream,
        and reset indent_level.

        No size parameter is accepted, and calling truncate
        always truncates to size 0.  To do otherwise would require
        keeping track of the indent level of past writes.
        """
        self.outputStream.truncate(0)
        self.indent_level=0

__all__=['PythonCodeOutputStream']
