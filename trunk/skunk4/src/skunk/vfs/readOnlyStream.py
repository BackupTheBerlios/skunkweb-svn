from cStringIO import StringIO
from vfs import VFSException

class ReadOnlyStream(object):
    def __init__(self, name, str=''):
        self._sio=StringIO(str)
        self.mode='r'
        self.name=name

    def __getattr__(self, attr):
        return getattr(self._sio, attr)

    def flush(self):
        raise VFSException, "unsupported operation: flush"

    def truncate(self, size=None):
        raise VFSException, "unsupported operation: truncate"

    def write(self, s):
        raise VFSException, "unsupported operation: write"

    def writelines(self, list):
        raise VFSException, "unsupported operation: writelines"

__all__=['ReadOnlyStream']
