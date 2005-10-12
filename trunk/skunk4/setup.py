import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, Extension

description="SkunkWeb Web Application Server Libraries"

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      license="BSD/GPL",
      name="SkunkWeb",
      url="http://skunkweb.org/",
      version="4.0a",
      zip_safe=True,
      keywords="cache skunk skunkweb web",
      ext_modules=[Extension('skunk.util.signal_plus',
                             ['src/skunk/util/signal_plus.c'])],
      namespace_packages=['skunk'],
      packages=['skunk',
                'skunk.cache',
                'skunk.date',
                'skunk.util'
                ],

# others later....      
#                'skunk.config',
#                'skunk.net',
#                'skunk.net.server',
#                'skunk.web',
#                'skunk.web.services']
#                ]
      package_dir={'' : 'src'})
