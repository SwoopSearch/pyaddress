"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import unittest
from pyaddress import Address, AddressParser


class AddressTest(unittest.TestCase):
    parser = None

    def setUp(self):
        self.parser = AddressParser()

    def test_basic_full_address(self):
        addr = Address("2 Park Street, Madison, WI 53703", self.parser)
        print addr.city, addr.state, addr.zip
        self.assertTrue(addr.house_number == "2")
        self.assertTrue(addr.street == "Park")
        self.assertTrue(addr.street_suffix == "Street")
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zip == 53703)


class AddressParserTest(unittest.TestCase):
    ap = None

    def setUp(self):
        self.ap = AddressParser()

    def test_load_suffixes(self):
        print self.ap.suffixes
        self.assertTrue(self.ap.suffixes["ALLEY"] == "ALY")

    def test_load_cities(self):
        self.assertTrue("wisconsin rapids" in self.ap.cities)

    def test_load_states(self):
        self.assertTrue(self.ap.states["Wisconsin"] == "WI")

    def test_load_streets(self):
        self.assertTrue("mifflin" in self.ap.streets)

if __name__ == '__main__':
    unittest.main()
