from distutils.core import setup

setup(
    name='pyaddress',
    version='0.1',
    packages=['pyaddress'],
    url='https://github.com/SwoopSearch/pyaddress',
    license='New BSD License',
    author='Swoop Search LLC, Josh Gachnang, Rob Jauquet',
    author_email='josh@swoopsrch.com',
    description='pyaddress is an address parsing library, taking the guesswork out of using addresses in your applications.',
    long_description=open('README.md').read(),
    package_data={'pyaddress': ['*.csv', 'README.md', 'LICENSE']}
)
