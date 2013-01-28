from distutils.core import setup

setup(
    name='address',
    version='0.1.0',
    url='https://github.com/SwoopSearch/pyaddress',
    license='New BSD License',
    author='Swoop Search LLC, Josh Gachnang, Rob Jauquet',
    author_email='josh@swoopsrch.com',
    description='address is an address parsing library, taking the guesswork out of using addresses in your applications.',
    long_description=open('README.rst', 'rt').read(),
    #data_files=[('', ['README.rst','pyaddress/cities.csv', 'pyaddress/suffixes.csv', 'pyaddress/streets.csv', 'pyaddress/tests.py', 'pyaddress/test_list.py'])],
    packages=['address'],
    test_suite='nose.collector',
    tests_require=['nose'],
)
