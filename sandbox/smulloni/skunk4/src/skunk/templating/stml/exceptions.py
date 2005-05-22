class SignatureError(Exception):
    pass

class LexicalError(Exception):
    def __init__(self, msg, offset, lineno):
        Exception.__init__(self, msg)
        self.offset=offset
        self.lineno=lineno

class ParseError(Exception):
    def __init__(self, msg, offset, lineno):
        Exception.__init__(self, msg)
        self.offset=offset
        self.lineno=lineno

class STMLSyntaxError(Exception):
    pass
