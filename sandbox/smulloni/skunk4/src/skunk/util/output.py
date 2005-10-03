"""

an output stream with thread-local backends.
Useful for redirecting stdout.

"""
from threading import local
from cStringIO import StringIO

class Output(object):
    _local=local()

    @classmethod
    def _get_output_stream(cls):
        loc=cls._local
        try:
            return loc.output
        except AttributeError:
            o=loc.output=StringIO()
            return o

    def write(self, str):
        self._get_output_stream().write(str)

    def __getattr__(self, attr):
        return getattr(self._get_output_stream(), attr)

    def __str__(self):
        return self._get_output_stream().getvalue()

    def reset(self):
        stream=self._get_output_stream()
        stream.seek(0)
        stream.truncate()

