from distutils.core import setup

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
      version='1.',
      packages=['PyDO'],
      package_dir={'' : 'src'})
