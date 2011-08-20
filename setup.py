from setuptools import setup, find_packages
import os

version = '2.0dev'
shortdesc = "An alternative to mixin-based extension of classes."
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name='plumber',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Python Software Foundation License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        ], # Get strings from http://www.python.org/pypi?:action=list_classifiers
      keywords='',
      author='Florian Friesdorf',
      author_email='flo@chaoflow.net',
      url='http://github.com/chaoflow/plumber',
      license='BSD license',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=True,
      install_requires=[
        'setuptools',
        ],
      extras_require={
        'test': [
            'interlude',
            'plone.testing',
            'unittest2',
            'zope.interface',
            ],
        },
      entry_points="""
      """,
      )
