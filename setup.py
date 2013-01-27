from setuptools import setup


setup(name='pyramid_es',
      version='0.1',
      description='Elasticsearch integration for Pyramid, via pyes.',
      long_description='',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Framework :: Pyramid',
          'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
      ],
      keywords='pyramid search pyes elasticsearch',
      url='http://github.com/cartlogic/pyramid_es',
      author='Scott Torborg',
      author_email='scott@cartlogic.com',
      install_requires=[
          'pyramid',
          'pyes',
          # These are for tests.
          'coverage',
          'nose>=1.1',
          'nose-cover3',
      ],
      license='MIT',
      packages=['pyramid_es'],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
