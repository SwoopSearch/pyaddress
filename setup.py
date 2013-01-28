from distutils.core import setup

setup(
    name='pyaddress',
    version='0.1.4',
    py_modules=['pyaddress'],
    url='https://github.com/SwoopSearch/pyaddress',
    license='New BSD License',
    author='Swoop Search LLC, Josh Gachnang, Rob Jauquet',
    author_email='josh@swoopsrch.com',
    description='pyaddress is an address parsing library, taking the guesswork out of using addresses in your applications.',
    long_description=open('README.rst', 'rt').read(),
    data_files=[('', ['README.rst','cities.csv', 'suffixes.csv', 'streets.csv', 'tests.py', 'test_list.py'])]
)
