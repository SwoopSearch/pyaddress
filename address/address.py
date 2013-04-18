# Meant to parse out address lines, minus city,state,zip into a usable dict for address matching
# Ignores periods and commas, because no one cares.

import re
import csv
import os
import dstk

# Keep lowercase, no periods
# Requires numbers first, then option dash plus numbers.
street_num_regex = r'(\d+)(-?)(\d*)'

apartment_regex_number = r'(#?)(\d*)(\w*)'
cwd = os.path.dirname(os.path.realpath(__file__))


class AddressParser(object):
    """
    AddressParser will be use to create Address objects. It contains a list of preseeded cities, states, prefixes,
    suffixes, and street names that will help the Address object correctly parse the given string. It is loaded
    with defaults that work in the average case, but can be adjusted for specific cases.
    """
    suffixes = {}
    # Lower case list of cities, used as a hint
    cities = []
    # Lower case list of streets, used as a hint
    streets = []
    prefixes = {
        "n": "N.", "e": "E.", "s": "S.", "w": "W.", "ne": "NE.", "nw": "NW.", 'se': "SE.", 'sw': "SW.", 'north': "N.",
        'east': "E.", 'south': "S.",
        'west': "W.", 'northeast': "NE.", 'northwest': "NW.", 'southeast': "SE.", 'southwest': "SW."}
    states = {
        'Mississippi': 'MS', 'Oklahoma': 'OK', 'Delaware': 'DE', 'Minnesota': 'MN', 'Illinois': 'IL', 'Arkansas': 'AR',
        'New Mexico': 'NM', 'Indiana': 'IN', 'Maryland': 'MD', 'Louisiana': 'LA', 'Idaho': 'ID', 'Wyoming': 'WY',
        'Tennessee': 'TN', 'Arizona': 'AZ', 'Iowa': 'IA', 'Michigan': 'MI', 'Kansas': 'KS', 'Utah': 'UT',
        'Virginia': 'VA', 'Oregon': 'OR', 'Connecticut': 'CT', 'Montana': 'MT', 'California': 'CA',
        'Massachusetts': 'MA', 'West Virginia': 'WV', 'South Carolina': 'SC', 'New Hampshire': 'NH',
        'Wisconsin': 'WI', 'Vermont': 'VT', 'Georgia': 'GA', 'North Dakota': 'ND', 'Pennsylvania': 'PA',
        'Florida': 'FL', 'Alaska': 'AK', 'Kentucky': 'KY', 'Hawaii': 'HI', 'Nebraska': 'NE', 'Missouri': 'MO',
        'Ohio': 'OH', 'Alabama': 'AL', 'New York': 'NY', 'South Dakota': 'SD', 'Colorado': 'CO', 'New Jersey': 'NJ',
        'Washington': 'WA', 'North Carolina': 'NC', 'District of Columbia': 'DC', 'Texas': 'TX', 'Nevada': 'NV',
        'Maine': 'ME', 'Rhode Island': 'RI'}

    def __init__(self, suffixes=None, cities=None, streets=None, backend="default", dstk_api_base=None, logger=None, required_confidence=0.65):
        """
        suffixes, cities and streets provide a chance to use different lists than the provided lists.
        suffixes is probably good for most users, unless you have some suffixes not recognized by USPS.
        cities is a very expansive list that may lead to false positives in some cases. If you only have a few cities
        you know will show up, provide your own list for better accuracy. If you are doing addresses across the US,
        the provided list is probably better.
        streets can be used to limit the list of possible streets the address are on. It comes blank by default and
        uses positional clues instead. If you are instead just doing a couple cities, a list of all possible streets
        will decrease incorrect street names.
        Valid backends include "default" and "dstk". If backend is dstk, it requires a dstk_api_base. Example of
        dstk_api_base would be 'http://example.com'.
        """
        self.logger = logger
        self.backend = backend
        self.dstk_api_base = dstk_api_base
        self.required_confidence = required_confidence
        if suffixes:
            self.suffixes = suffixes
        else:
            self.load_suffixes(os.path.join(cwd, "suffixes.csv"))
        if cities:
            self.cities = cities
        else:
            self.load_cities(os.path.join(cwd, "cities.csv"))
        if streets:
            self.streets = streets
        else:
            self.load_streets(os.path.join(cwd, "streets.csv"))
        if backend == "dstk":
            if dstk_api_base is None:
                raise ValueError("dstk_api_base is required for dstk backend.")
            self.dstk = dstk.DSTK({'apiBase': dstk_api_base})
        elif backend == "default":
            pass
        else:
            raise ValueError("backend must be either 'default' or 'dstk'.")

    def parse_address(self, address, line_number=-1):
        """
        Return an Address object from the given address. Passes itself to the Address constructor to use all the custom
        loaded suffixes, cities, etc.
        """
        return Address(address, self, line_number, self.logger)

    def dstk_multi_address(self, address_list):
        if self.backend != "dstk":
            raise ValueError("Only allowed for DSTK backends.")
        if self.logger: self.logger.debug("Sending {0} possible addresses to DSTK".format(len(address_list)))
        multi_address = self.dstk.street2coordinates(address_list)
        if self.logger: self.logger.debug("Received {0} addresses from DSTK".format(len(multi_address)))
        # if self.logger: self.logger.debug("End street2coords")
        addresses = []
        # if self.logger: self.logger.debug("Multi Addresses: {0}".format(multi_address))
        for address, dstk_return in multi_address.items():
            try:
                if dstk_return is None:
                    # if self.logger: self.logger.debug("DSTK None return for: {0}".format(address))
                    continue
                addresses.append(Address(address, self, -1, self.logger, dstk_pre_parse=dstk_return))
                if self.logger: self.logger.debug("DSTK Address Appended: {0}".format(dstk_return))
            except InvalidAddressException as e:
                # if self.logger: self.logger.debug("Error from dstk Address: {0}".format(e.message))
                continue
            except DSTKConfidenceTooLowException as e:
                continue
        return addresses


    def load_suffixes(self, filename):
        """
        Build the suffix dictionary. The keys will be possible long versions, and the values will be the
        accepted abbreviations. Everything should be stored using the value version, and you can search all
        by using building a set of self.suffixes.keys() and self.suffixes.values().
        """
        with open(filename, 'r') as f:
            for line in f:
                # Make sure we have key and value
                if len(line.split(',')) != 2:
                    continue
                    # Strip off newlines.
                self.suffixes[line.strip().split(',')[0]] = line.strip().split(',')[1]

    def load_cities(self, filename):
        """
        Load up all cities in lowercase for easier matching. The file should have one city per line, with no extra
        characters. This isn't strictly required, but will vastly increase the accuracy.
        """
        with open(filename, 'r') as f:
            for line in f:
                self.cities.append(line.strip().lower())

    def load_streets(self, filename):
        """
        Load up all streets in lowercase for easier matching. The file should have one street per line, with no extra
        characters. This isn't strictly required, but will vastly increase the accuracy.
        """
        with open(filename, 'r') as f:
            for line in f:
                self.streets.append(line.strip().lower())


# Procedure: Go through backwards. First check for apartment number, then
# street suffix, street name, street prefix, then building. For each sub,
# check if that spot is already filled in the dict.
class Address:
    unmatched = False
    house_number = None
    street_prefix = None
    street = None
    street_suffix = None
    apartment = None
    # building = None
    city = None
    state = None
    zip = None
    original = None
    # Only set for dstk
    lat = None
    lng = None
    last_matched = None
    unmatched = False
    # Only used for debug
    line_number = -1
    # Confidence value from DSTK. 0 - 1, -1 for not set.
    confidence = -1

    def __init__(self, address, parser, line_number=-1, logger=None, dstk_pre_parse=None):
        """
        @dstk_pre_parse: a single value from a dstk multiple street2coordinates return. @address would be the key then.
        """
        self.parser = parser
        self.line_number = line_number
        self.original = self._clean(address)
        self.logger = logger
        if address is None:
            return
        address = self.preprocess_address(address)
        if parser.backend == "dstk":
            # if self.logger: self.logger.debug("Preparsed: {0}".format(dstk_pre_parse))
            self.dstk_parse(address, parser, pre_parsed_address=dstk_pre_parse)
        elif parser.backend == "default":
            self.parse_address(address)
        else:
            raise ValueError("Parser gave invalid backend, must be either 'default' or 'dstk'.")

        if self.house_number is None or self.house_number <= 0:
            raise InvalidAddressException("Addresses must have house numbers.")
        elif self.street is None or self.street == "":
            raise InvalidAddressException("Addresses must have streets.")
            # if self.house_number is None or self.street is None or self.street_suffix is None:
            # raise ValueError("Street addresses require house_number, street, and street_suffix")

    def parse_address(self, address):
        # print "YOU ARE PARSING AN ADDRESS"
        # Save the original string

        # Get rid of periods and commas, split by spaces, reverse.
        # Periods should not exist, remove them. Commas separate tokens. It's possible we can use commas for better guessing.
        address = address.strip().replace('.', '')
        # We'll use this for guessing.
        self.comma_separated_address = address.split(',')
        address = address.replace(',', '')

        # First, do some preprocessing
        # address = self.preprocess_address(address)

        # Try all our address regexes. USPS says parse from the back.
        address = reversed(address.split())
        # Save unmatched to process after the rest is processed.
        unmatched = []
        # Use for contextual data
        for token in address:
        #            print token, self
            # Check zip code first
            if self.check_zip(token):
                continue
            if self.check_state(token):
                continue
            if self.check_city(token):
                continue
            if self.check_street_suffix(token):
                continue
            if self.check_house_number(token):
                continue
            if self.check_street_prefix(token):
                continue
            if self.check_street(token):
                continue
                # if self.check_building(token):
            #     continue
            if self.guess_unmatched(token):
                continue
            unmatched.append(token)

        # Post processing

        for token in unmatched:
        #            print "Unmatched token: ", token
            if self.check_apartment_number(token):
                continue
                # print "Unmatched token: ", token
            #            print "Original address: ", self.original
            self.unmatched = True

    def preprocess_address(self, address):
        """
        Takes a basic address and attempts to clean it up, extract reasonably assured bits that may throw off the
        rest of the parsing, and return the cleaned address.
        """
        # Run some basic cleaning
        address = address.replace("# ", "#")
        address = address.replace(" & ", "&")
        # Clear the address of things like 'X units', which shouldn't be in an address anyway. We won't save this for now.
        if re.search(r"-?-?\w+ units", address, re.IGNORECASE):
            address = re.sub(r"-?-?\w+ units", "", address, flags=re.IGNORECASE)
            # Sometimes buildings are put in parantheses.
        # building_match = re.search(r"\(.*\)", address, re.IGNORECASE)
        # if building_match:
        #     self.building = self._clean(building_match.group().replace('(', '').replace(')', ''))
        #     address = re.sub(r"\(.*\)", "", address, flags=re.IGNORECASE)
        # Now let's get the apartment stuff out of the way. Using only sure match regexes, delete apartment parts from
        # the address. This prevents things like "Unit" being the street name.
        apartment_regexes = [r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                             r'style\s\w{1,2}', r'townhouse style\s\w{1,2}']
        for regex in apartment_regexes:
            apartment_match = re.search(regex, address, re.IGNORECASE)
            if apartment_match:
            #                print "Matched regex: ", regex, apartment_match.group()
                self.apartment = self._clean(apartment_match.group())
                address = re.sub(regex, "", address, flags=re.IGNORECASE)
            # Now check for things like ",  ," which throw off dstk
        address = re.sub(r"\,\s*\,", ",", address)
        return address

    def check_zip(self, token):
        """
        Returns true if token is matches a zip code (5 numbers). Zip code must be the last token in an address (minus anything
        removed during preprocessing such as --2 units.
        """
        if self.zip is None:
            # print "last matched", self.last_matched
            if self.last_matched is not None:
                return False
                # print "zip check", len(token) == 5, re.match(r"\d{5}", token)
            if len(token) == 5 and re.match(r"\d{5}", token):
                self.zip = self._clean(token)

                return True
        return False

    def check_state(self, token):
        """
        Check if state is in either the keys or values of our states list. Must come before the suffix.
        """
        # print "zip", self.zip
        if len(token) == 2 and self.state is None:
            if token.capitalize() in self.parser.states.keys():
                self.state = self._clean(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state = self._clean(token.upper())
                return True
        if self.state is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.capitalize() in self.parser.states.keys():
                self.state = self._clean(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state = self._clean(token.upper())
                return True
        return False

    def check_city(self, token):
        """
        Check if there is a known city from our city list. Must come before the suffix.
        """
        shortened_cities = {'saint': 'st.'}
        if self.city is None and self.state is not None and self.street_suffix is None:
            if token.lower() in self.parser.cities:
                self.city = self._clean(token.capitalize())
                return True
            return False
            # Check that we're in the correct location, and that we have at least one comma in the address
        if self.city is None and self.apartment is None and self.street_suffix is None and len(
                self.comma_separated_address) > 1:
            if token.lower() in self.parser.cities:
                self.city = self._clean(token.capitalize())
                return True
            return False
        # Multi word cities
        if self.city is not None and self.street_suffix is None and self.street is None:
            print "Checking for multi part city", token.lower(), token.lower() in shortened_cities.keys()
            if token.lower() + ' ' + self.city in self.parser.cities:
                self.city = self._clean((token.lower() + ' ' + self.city).capitalize())
                return True
            if token.lower() in shortened_cities.keys():
                token = shortened_cities[token.lower()]
                print "Checking for shorted multi part city", token.lower() + ' ' + self.city
                if token.lower() + ' ' + self.city.lower() in self.parser.cities:
                    self.city = self._clean(token.capitalize() + ' ' + self.city.capitalize())
                    return True

    def check_apartment_number(self, token):
        """
        Finds apartment, unit, #, etc, regardless of spot in string. This needs to come after everything else has been ruled out,
        because it has a lot of false positives.
        """
        apartment_regexes = [r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                             r'style\s\w{1,2}', r'\d{1,4}/\d{1,4}', r'\d{1,4}', r'\w{1,2}']
        for regex in apartment_regexes:
            if re.match(regex, token.lower()):
                self.apartment = self._clean(token)
                return True
            #        if self.apartment is None and re.match(apartment_regex_number, token.lower()):
            ##            print "Apt regex"
            #            self.apartment = token
            #            return True
            ## If we come on apt or apartment and already have an apartment number, add apt or apartment to the front
        if self.apartment and token.lower() in ['apt', 'apartment']:
        #            print "Apt in a_n"
            self.apartment = self._clean(token + ' ' + self.apartment)
            return True

        if not self.street_suffix and not self.street and not self.apartment:
        #            print "Searching for unmatched term: ", token, token.lower(),
            if re.match(r'\d?\w?', token.lower()):
                self.apartment = self._clean(token)
                return True
        return False

    def check_street_suffix(self, token):
        """
        Attempts to match a street suffix. If found, it will return the abbreviation, with the first letter capitalized
        and a period after it. E.g. "St." or "Ave."
        """
        # Suffix must come before street
        # print "Suffix check", token, "suffix", self.street_suffix, "street", self.street
        if self.street_suffix is None and self.street is None:
            # print "upper", token.upper()
            if token.upper() in self.parser.suffixes.keys():
                suffix = self.parser.suffixes[token.upper()]
                self.street_suffix = self._clean(suffix.capitalize() + '.')
                return True
            elif token.upper() in self.parser.suffixes.values():
                self.street_suffix = self._clean(token.capitalize() + '.')
                return True
        return False

    def check_street(self, token):
        """
        Let's assume a street comes before a prefix and after a suffix. This isn't always the case, but we'll deal
        with that in our guessing game. Also, two word street names...well...

        This check must come after the checks for house_number and street_prefix to help us deal with multi word streets.
        """
        # First check for single word streets between a prefix and a suffix
        if self.street is None and self.street_suffix is not None and self.street_prefix is None and self.house_number is None:
            self.street = self._clean(token.capitalize())
            return True
        # Now check for multiple word streets. This check must come after the check for street_prefix and house_number for this reason.
        elif self.street is not None and self.street_suffix is not None and self.street_prefix is None and self.house_number is None:
            self.street = self._clean(token.capitalize() + ' ' + self.street)
            return True
        if not self.street_suffix and not self.street and token.lower() in self.parser.streets:
            self.street = self._clean(token)
            return True
        return False

    def check_street_prefix(self, token):
        """
        Finds street prefixes, such as N. or Northwest, before a street name. Standardizes to 1 or two letters, followed
        by a period.
        """
        if self.street and not self.street_prefix and token.lower().replace('.', '') in self.parser.prefixes.keys():
            self.street_prefix = self._clean(self.parser.prefixes[token.lower().replace('.', '')])
            return True
        return False

    def check_house_number(self, token):
        """
        Attempts to find a house number, generally the first thing in an address. If anything is in front of it,
        we assume it is a building name.
        """
        if self.street and self.house_number is None and re.match(street_num_regex, token.lower()):
            if '/' in token:
                token = token.split('/')[0]
            if '-' in token:
                token = token.split('-')[0]
            self.house_number = self._clean(str(token))
            return True
        return False

    def check_building(self, token):
        """
        Building name check. If we have leftover and everything else is set, probably building names.
        Allows for multi word building names.
        """
        if self.street and self.house_number:
            if not self.building:
                self.building = self._clean(token)
            else:
                self.building = self._clean(token + ' ' + self.building)
            return True
        return False

    def guess_unmatched(self, token):
        """
        When we find something that doesn't match, we can make an educated guess and log it as such.
        """
        # Check if this is probably an apartment:
        if token.lower() in ['apt', 'apartment']:
            return False
            # Stray dashes are likely useless
        if token.strip() == '-':
            return True
            # Almost definitely not a street if it is one or two characters long.
        if len(token) <= 2:
            return False
            # Let's check for a suffix-less street.
        if self.street_suffix is None and self.street is None and self.street_prefix is None and self.house_number is None:
            # Streets will just be letters
            if re.match(r"[A-Za-z]", token):
                if self.line_number >= 0:
                    pass
                #                    print "{0}: Guessing suffix-less street: ".format(self.line_number), token
                else:
                #                    print "Guessing suffix-less street: ", token
                    pass
                self.street = self._clean(token.capitalize())
                return True
        return False

    def full_address(self):
        """
        Print the address in a human readable format
        """
        addr = ""
        # if self.building:
        #     addr = addr + "(" + self.building + ") "
        if self.house_number:
            addr = addr + self.house_number
        if self.street_prefix:
            addr = addr + " " + self.street_prefix
        if self.street:
            addr = addr + " " + self.street
        if self.street_suffix:
            addr = addr + " " + self.street_suffix
        if self.apartment:
            addr = addr + " " + self.apartment
        if self.city:
            addr = addr + ", " + self.city
        if self.state:
            addr = addr + ", " + self.state
        if self.zip:
            addr = addr + " " + self.zip
        return addr

    def _clean(self, item):
        if item is None:
            return None
        else:
            return item.encode("utf-8", "replace")

    def __repr__(self):
        return unicode(self)

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        address_dict = {
            "house_number": self.house_number,
            "street_prefix": self.street_prefix,
            "street": self.street,
            "street_suffix": self.street_suffix,
            "apartment": self.apartment,
            # "building": self.building,
            "city": self.city,
            "state": self.state,
            "zip": self.zip
        }
        # print "Address Dict", address_dict
        return u"Address - House number: {house_number} Prefix: {street_prefix} Street: {street} Suffix: {street_suffix}" \
               u" Apartment: {apartment} City,State,Zip: {city}, {state} {zip}".format(**address_dict)

    def dstk_parse(self, address, parser, pre_parsed_address=None):
        """
        Given an address string, use DSTK to parse the address and then coerce it to a normal Address object.
        pre_parsed_address for multi parsed string. Gives the value part for single dstk return value. If
        pre_parsed_address is None, parse it via dstk on its own.
        """
        if pre_parsed_address:
            dstk_address = pre_parsed_address
        else:
            if self.logger: self.logger.debug("Asking DSTK for address parse {0}".format(address.encode("ascii", "ignore")))
            dstk_address = parser.dstk.street2coordinates(address)
            # if self.logger: self.logger.debug("dstk return: {0}".format(dstk_address))
        if 'confidence' not in dstk_address:
            raise InvalidAddressException("Could not deal with DSTK return: {0}".format(dstk_address))
        if dstk_address['street_address'] == "":
            raise InvalidAddressException("Empty street address in DSTK return: {0}".format(dstk_address))
        if dstk_address['street_number']  is None or dstk_address['street_name'] is None:
            raise InvalidAddressException("House number or street name was Non in DSTK return: {0}".format(dstk_address))
        if dstk_address['confidence'] < parser.required_confidence:
            raise DSTKConfidenceTooLowException("Required confidence: {0}. Got confidence: {1}. Address: {2}. Return: {3}.".format(parser.required_confidence, dstk_address['confidence'], address.encode("ascii", "ignore"), dstk_address))
        self.confidence = dstk_address['confidence']
        if 'street_address' in dstk_address:
            intersections = self._get_dstk_intersections(address, dstk_address['street_address'])
        if self.logger: self.logger.debug("Confidence: {0}.".format(dstk_address['confidence']))
        if self.logger: self.logger.debug("Address: {0}.".format(address))
        if self.logger: self.logger.debug("Return: {0}.".format(dstk_address))
        # if self.logger: self.logger.debug("")

        addr = dstk_address
        if addr is None:
            raise InvalidAddressException("DSTK could not parse address: {0}".format(self.original))
        if "street_number" in addr:
            if addr["street_number"] not in address:
                raise InvalidAddressException("DSTK returned a house number not in the original address: {0}".format(addr))
            self.house_number = addr["street_number"]
        else:
            raise InvalidAddressException("(dstk) Addresses must have house numbers: {0}".format(addr))

        if "locality" in addr:
            self.city = addr["locality"]
            # DSTK shouldn't be returning unknown cities
            if addr["locality"] not in address:
                raise InvalidAddressException("DSTK returned a city not in the address. City: {0}, Address: {1}.".format(self.city, address))
        if "region" in addr:
            self.state = addr["region"]
            # if "fips_county" in addr:
            # self.zip = addr["fips_county"]
        if "latitude" in addr:
            self.lat = addr["latitude"]
        if "longitude" in addr:
            self.lng = addr["longitude"]
            # Try and find the apartment
        # First remove the street_address (this doesn't include apartment)
        if "street_address" in addr:
            apartment = address.replace(addr["street_address"], '')
        # Make sure the city doesn't somehow come before the street in the original string.

            # try:
            #     end_pos = re.search("(" + addr["locality"] + ")", apartment).start(1) - 1
            #     # self.apartment = apartment[:end_pos]
            # except Exception:
            #     pass
            # self.apartment = None
        # Now that we have an address, try to parse out street suffix, prefix, and street
        if self.apartment:
            street_addr = addr["street_address"].replace(self.apartment, '')
        else:
            street_addr = addr["street_address"]

        # We should be left with only prefix, street, suffix. Go for suffix first.
        split_addr = street_addr.split()
        if len(split_addr) == 0:
            if self.logger: self.logger.debug("Could not split street_address: {0}".format(addr))
            raise InvalidAddressException("Could not split street_address: {0}".format(addr))
        # Get rid of house_number
        if split_addr[0] == self.house_number:
            split_addr = split_addr[1:]
        if self.logger: self.logger.debug("Checking {0} for suffixes".format(split_addr[-1].upper()))
        if split_addr[-1].upper() in parser.suffixes.keys() or split_addr[-1].upper() in parser.suffixes.values():
            self.street_suffix = split_addr[-1]
            split_addr = split_addr[:-1]
        if self.logger: self.logger.debug("Checking {0} for prefixes".format(split_addr[0].lower()))
        if split_addr[0].lower() in parser.prefixes.keys() or split_addr[0].upper() in parser.prefixes.values() or \
                                split_addr[0].upper() + '.' in parser.prefixes.values():
            if split_addr[0][-1] == '.':
                self.street_prefix = split_addr[0].upper()
            else:
                self.street_prefix = split_addr[0].upper() + '.'
            if self.logger: self.logger.debug("Saving prefix: {0}".format(self.street_prefix))
            split_addr = split_addr[1:]
        if self.logger: self.logger.debug("Saving street: {0}".format(split_addr))
        self.street = " ".join(split_addr)
        # DSTK shouldn't be guessing cities that come before streets.
        match = re.search(self.street, address)
        if match is None:
            raise InvalidAddressException("DSTK picked a street not in the original address. Street: {0}. Address: {1}.".format(self.street, address))
        street_position = match
        match = re.search(self.city, address)
        if match is None:
            raise InvalidAddressException("DSTK picked a city not in the original address. City: {0}. Address: {1}.".format(self.city, address))
        city_position = match
        if city_position.start(0) < street_position.end(0):
            raise InvalidAddressException("DSTK picked a street that comes after the city. Street: {0}. City: {1}. Address: {2}.".format(self.street, self.city, address))
        if self.logger: self.logger.debug("Successful DSTK address: {0}, house: {1}, street: {2}\n".format(self.original, self.house_number, self.street))

    def _get_dstk_intersections(self, address, dstk_address):
        """
        Find the unique tokens in the original address and the returned address.
        """
        # Normalize both addresses
        normalized_address = self._normalize(address)
        normalized_dstk_address = self._normalize(dstk_address)
        address_uniques = set(normalized_address) - set(normalized_dstk_address)
        dstk_address_uniques = set(normalized_dstk_address) - set(normalized_address)
        if self.logger: self.logger.debug("Address Uniques {0}".format(address_uniques))
        if self.logger: self.logger.debug("DSTK Address Uniques {0}".format(dstk_address_uniques))
        return (len(address_uniques), len(dstk_address_uniques))

    def _normalize(self, address):
        """
        Normalize prefixes, suffixes and other to make matching original to returned easier.
        """
        normalized_address = []
        if self.logger: self.logger.debug("Normalizing Address: {0}".format(address))
        for token in address.split():
            if token.upper() in self.parser.suffixes.keys():
                normalized_address.append(self.parser.suffixes[token.upper()].lower())
            elif token.upper() in self.parser.suffixes.values():
                normalized_address.append(token.lower())
            elif token.upper().replace('.', '') in self.parser.suffixes.values():
                normalized_address.append(token.lower().replace('.', ''))
            elif token.lower() in self.parser.prefixes.keys():
                normalized_address.append(self.parser.prefixes[token.lower()].lower())
            elif token.upper() in self.parser.prefixes.values():
                normalized_address.append(token.lower()[:-1])
            elif token.upper() + '.' in self.parser.prefixes.values():
                normalized_address.append(token.lower())
            else:
                normalized_address.append(token.lower())
        return normalized_address


def create_cities_csv(filename="places2k.txt", output="cities.csv"):
    """
    Takes the places2k.txt from USPS and creates a simple file of all cities.
    """
    with open(filename, 'r') as city_file:
        with open(output, 'w') as out:
            for line in city_file:
                # Drop Puerto Rico (just looking for the 50 states)
                if line[0:2] == "PR":
                    continue
                    # Per census.gov, characters 9-72 are the name of the city or place. Cut ,off the last part, which is city, town, etc.
                #                    print " ".join(line[9:72].split()[:-1])
                out.write(" ".join(line[9:72].split()[:-1]) + '\n')


class InvalidAddressException(Exception):
    pass

class DSTKConfidenceTooLowException(Exception):
    pass