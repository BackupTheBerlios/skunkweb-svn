from distutils.core import setup, Extension

description="SkunkWeb Web Application Server Libraries"

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      license="BSD/GPL",
      name="SkunkWeb",
      url="http://skunkweb.org/",
      version="4.0a",
      ext_modules=[Extension('skunk.util.signal_plus',
                             ['src/skunk/util/signal_plus.c'])],
      packages=['skunk',
                'skunk.config',
                'skunk.net',
                'skunk.net.server',
                'skunk.util',
                'skunk.web',
                'skunk.web.services',
                'skunk.web.services.requestHandler'],
      package_dir={'' : 'src'})
