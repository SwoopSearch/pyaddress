from distutils.core import setup

setup(
    name='address',
    version='0.1.1',
    url='https://github.com/SwoopSearch/pyaddress',
    author='Swoop Search LLC, Josh Gachnang, Rob Jauquet',
    author_email='Josh@SwoopSrch.com',
    description='address is an address parsing library, taking the guesswork out of using addresses in your applications.',
    long_description=open('README.rst', 'rt').read(),
    #data_files=[('', ['README.rst','pyaddress/cities.csv', 'pyaddress/suffixes.csv', 'pyaddress/streets.csv', 'pyaddress/tests.py', 'pyaddress/test_list.py'])],
    packages=['address'],
    package_dir={'address': 'address'},
    package_data={'address': ['cities.csv', 'streets.csv', 'suffixes.csv']},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing",
    ],
    keywords = "example documentation tutorial",
    maintainer="Swoop Search LLC, Josh Gachnang, Rob Jauquet",
    maintainer_email="Josh@SwoopSrch.com",
)
