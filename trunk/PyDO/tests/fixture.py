from pydo.dbi import getConnection

class Fixture(object):

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        pass

    def db():
        def fget(self):
            return getConnection('pydotest')
        return fget
    db=property(db())

    def __call__(self):
        self.setup()
        try:
            self.run()
        finally:
            self.cleanup()
            
