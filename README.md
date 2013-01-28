pyaddress
=========

pyaddress is an address parsing library, taking the guesswork out of using addresses in your applications. We use it as part of our apartment search and apartment spider applications.

Example
-------

First, we create an AddressParser. AddressParsers allow us to feed in lists of cities, streets, and address suffixes

```python
from pyaddress import AddressParser, Address

ap = AddressParser()
address = ap.parse_address('123 West Mifflin Street, Madison, WI, 53703')
print "Address is: {0} {1} {2} {3}".format(address.house_number, address.street_prefix, address.street, address.street_suffix)

> Address is: 123 W. Mifflin St.
```

AddressParser
-------------

`AddressParser(self, suffixes=None, cities=None, streets=None)`

suffixes, cities, and streets all accept lists as arguments. If you leave them as none, they will read default files
from the package, namely suffixes.csv, cities.csv, and streets.csv. Streets is intentionally blank.

You can provide lists of acceptable suffixes, cities, and streets to lower your false positives. If you know all
the addresses you are processing are in a small area, you can provide a list of the cities in the area and should
get more accurate results. If you are only doing one city, you could provide that single city in a list, and a list
of all streets in that city.


Address
-------

Addresses get returned by AddressParser.parser_address(). They have the following attributes:

`house_number`

The number on a house. This is required for all valid addresses. E.g. __123__ W. Mifflin St.

> street_prefix

The direction before the street name. Always represented as one or two letters followed by a period. Not required.
E.g. 123 __W.__ Mifflin St.

> street

The name of the street. Potentially multiple words. This is required for a valid address. E.g. 123 W. __Mifflin__ St.

> street_suffix

The ending of a street. This will always be the USPS abbreviation followed by a period. Not required, but highly recommended.
 E.g. 123 W. Mifflin __St.__

> apartment

Apartment number or unit style or any number of things signifying a specific part of an address. Not required. E.g. 123
W. Mifflin St. __Apt 10__

> buiding

Sometimes addresses are grouped into buildings, or are more commonly known as by building names. Not required, and often
 in parathenses. E.g. 123 W. Mifflin St. Apt 10 __(The Estates)__

> city

The city part of the address, preferably following a comma. E.g. 123 W. Mifflin St., __Madison__, WI 53703

> state

The state of the address, preferably following the city and a comma. Always two capitalized letters. E.g. 123 W. Mifflin St., Madison, __WI__ 53703

> zip

The 5 digit zip code of the address, preferably following the state. 9 digit zips not yet supported. E.g. 123 W. Mifflin St., Madison, WI __53703__

> full_address()

Returns a human readable version of the address for display. Follows the same style rules as the above attributes.
Example return: (The Estates) 123 W. Mifflin St. Apt 10, Madison, WI 53703
