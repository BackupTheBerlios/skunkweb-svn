from gzip import GzipFile, write32u, FNAME

class TimelessGzipFile(GzipFile):
    """unfortunate hack -- gzip writes the current
    time into the gzip header.  This clones
    the method from the gzip module that does that, but
    just writes 0."""
    def _write_gzip_header(self):
        self.fileobj.write('\037\213')             # magic header
        self.fileobj.write('\010')                 # compression method
        fname = self.filename[:-3]
        flags = 0
        if fname:
            flags = FNAME
        self.fileobj.write(chr(flags))
        # don't use current time!
        write32u(self.fileobj, 0L)
        self.fileobj.write('\002')
        self.fileobj.write('\377')
        if fname:
            self.fileobj.write(fname + '\000')
    
