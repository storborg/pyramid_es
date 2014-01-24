from setuptools import setup, find_packages


setup(name='pyramid_es',
      version='0.2.1',
      description='Elasticsearch integration for Pyramid.',
      long_description=open('README.rst').read(),
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Framework :: Pyramid',
          'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
      ],
      keywords='pyramid search elasticsearch',
      url='http://github.com/cartlogic/pyramid_es',
      author='Scott Torborg',
      author_email='scott@cartlogic.com',
      install_requires=[
          'pyramid',
          'sqlalchemy',
          'six',
          # Pinned version for now because elasticsearch wrappers seem to have
          # the worst API stability of any software known to man. Let's hope
          # this one is better.
          'elasticsearch==0.4.4',
      ],
      license='MIT',
      packages=find_packages(),
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
