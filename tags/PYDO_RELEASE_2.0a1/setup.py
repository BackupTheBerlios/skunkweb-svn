from distutils.core import setup
import sys
sys.path.insert(0, 'src')
from PyDO2 import __version__ as version
description='a Python ORM supporting many RDBMS backends'
keywords=['ORM',
          'database',
          'SkunkWeb']
   

setup(author='Drew Csillag',
      author_email='drew_csillag@yahoo.com',
      maintainer='Jacob Smullyan',
      maintainer_email='smulloni@smullyan.org',
      description=description,
      keywords=keywords,
      license='GPL/BSD',
      name='PyDO',
      url='http://skunkweb.org/PyDO.html',
      version=version,
      packages=['PyDO2', 'PyDO2.drivers'],
      package_dir={'' : 'src'})
