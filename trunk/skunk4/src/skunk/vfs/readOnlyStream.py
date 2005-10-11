from cStringIO import StringIO
from vfs import VFSException

class ReadOnlyStream(object):
    def __init__(self, name, str=''):
        self._sio=StringIO(str)
        self.closed=0
        self.mode='r'
        self.name=name

    def read(self, n=-1):
        return self._sio.read(n)

    def readline(self, length=None):
        return self._sio.readline(length)

    def readlines(self, sizehint=0):
        return self._sio.readlines(sizehint)

    def close(self):
        self._sio.close()
        self.closed=1

    def flush(self):
        raise VFSException, "unsupported operation: flush"

    def isatty(self):
        return self._sio.isatty()

    def seek(self, pos, mode=0):
        self._sio.seek(pos, mode)

    def tell(self):
        return self._sio.tell()

    def truncate(self, size=None):
        raise VFSException, "unsupported operation: truncate"

    def write(self, s):
        raise VFSException, "unsupported operation: write"

    def writelines(self, list):
        raise VFSException, "unsupported operation: writelines"

    def __iter__(self):
        return self._sio.__iter__()

__all__=['ReadOnlyStream']
