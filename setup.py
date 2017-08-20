from setuptools import setup, find_packages


long_description = '''Please see
`the documentation <http://pyramid-es.readthedocs.org/en/latest/>`_.
'''


setup(name='pyramid_es',
      version='0.3.2.dev',
      description='Elasticsearch integration for Pyramid.',
      long_description=long_description,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Framework :: Pyramid',
          'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
      ],
      keywords='pyramid search elasticsearch',
      url='http://github.com/storborg/pyramid_es',
      author='Scott Torborg',
      author_email='storborg@gmail.com',
      install_requires=[
          'pyramid>=1.4',
          'pyramid_tm',
          'transaction',
          'sqlalchemy>=0.8',
          'six>=1.5.2',
          'elasticsearch>=1.0.0,<2.0.0',
      ],
      license='MIT',
      packages=find_packages(),
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
