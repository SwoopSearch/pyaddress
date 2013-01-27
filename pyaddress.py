# Meant to parse out address lines, minus city,state,zip into a usable dict for address matching
# Ignores periods and commas, because no one cares.

import re
import csv

# Keep lowercase, no periods
# Requires numbers first, then option dash plus numbers.
street_num_regex = r'(\d+)(-*)(\d*)'

apartment_name = ['apartment', 'apt']
apartment_regex_number = r'(#?)(\d*)(\w*)'


zip_regex = r'(\d){5}'

parentheses_buiding_regex = r"\(.*\)"


class AddressParser(object):
    suffixes = {}
    # Lower case list of cities, used as a hint
    cities = []
    # Lower case list of streets, used as a hint
    streets = []
    prefixes = {
        "n": "N.", "e": "E.", "s": "S.", "w": "W.", "ne": "NE.", "nw": "NW.", 'se': "SE.", 'sw': "SW.", 'north': "N.", 'east': "E.", 'south': "S.",
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

    def __init__(self, suffixes=None, cities=None, streets=None):
        if suffixes:
            self.suffixes = suffixes
        else:
            self.load_suffixes("address_suffixes.csv")
        if cities:
            self.cities = cities
        else:
            self.load_cities("cities.csv")
        if streets:
            self.streets = streets
        else:
            self.load_streets("streets.csv")

    def parse_address(self, address):
        """
        Return an Address object from the given address. Passes itself to the Address constructor to use all the custom
        loaded suffixes, cities, etc.
        """
        return Address(address, self)

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
    building = None
    city = None
    state = None
    zip = None
    original = None
    last_matched = None

    def __init__(self, address, parser):
        self.parser = parser
        parsed_address = self.parse_address(address)
        # Take all the keys in the returned dict and make them class attributes
        if parsed_address:
            for key in parsed_address:
                setattr(self, key, parsed_address[key])
        # if self.house_number is None or self.street is None or self.street_suffix is None:
            # raise ValueError("Street addresses require house_number, street, and street_suffix")

    def parse_address(self, address):
        # Get rid of periods and commas, split by spaces, reverse.
        # Periods should not exist, remove them. Commas separate tokens. It's possible we can use commas for better guessing.
        address = address.strip().replace('.', '')
        # We'll use this for guessing.
        self.comma_separated_address = address.split(',')
        address = address.replace(',', '')


        # Save the original string
        self.original = address
        # Run some basic cleaning
        address = address.replace("# ", "#")
        address = address.replace(" & ", "&")

        # Try all our address regexes. USPS says parse from the back.
        address = reversed(address.split())
        # Save unmatched to process after the rest is processed.
        unmatched = []
        # Use for contextual data
        for token in address:
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
            if self.check_building(token):
                continue
            if self.guess_unmatched(token):
                continue
            unmatched.append(token)

        # Post processing
        for token in unmatched:
            if self.check_apartment_number(token):
                continue
            print "Unmatched term: ", token

    def check_zip(self, token):
        """
        Returns true if token is matches a zip code (5 numbers). Zip code must be the last token in an address.
        """
        if self.zip is None:
            if self.last_matched is not None:
                return False
            if len(token) == 5 and re.match(zip_regex, token):
                self.zip = token
                return True
        return False

    def check_state(self, token):
        """
        Check if state is in either the keys or values of our states list.
        """
        if self.state is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.capitalize() in self.parser.states.keys():
                self.state = self.parser.states[token.capitalize()]
                return True
            elif token.upper() in self.parser.states.values():
                self.state = token.upper()
                return True
        return False

    def check_city(self, token):
        # Check that we're in the correct location, and that we have at least one comma in the address
        if self.apartment is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.lower() in self.parser.cities:
                self.city = token.capitalize()
                return True
            return False

    def check_apartment_number(self, token):
        apartment_regexes = [r'#\w+ & \w+', '#\w+ Rm \w+', "#\w+-\w", r'Apt #{0,1}\w+', r'Apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'Rm \w+', r'RM \w+', r'Unit #?\w+', r'- #{0,1}\w+', r'No\s?\d+\w*', r'Style\s\w{1,2}']
        for regex in apartment_regexes:
            if re.match(regex, token):
                self.apartment = token
                return True
#        if self.apartment is None and re.match(apartment_regex_number, token.lower()):
##            print "Apt regex"
#            self.apartment = token
#            return True
        ## If we come on apt or apartment and already have an apartment number, add apt or apartment to the front
        if self.apartment and token.lower() in apartment_name:
#            print "Apt in a_n"
            self.apartment = token + ' ' + self.apartment
            return True

        if not self.street_suffix and not self.street and not self.apartment:
#            print "Searching for unmatched term: ", token, token.lower(),
            if re.match(r'\d?\w?', token.lower()):
                self.apartment = token
                return True
        return False

    def check_street_suffix(self, token):
        """
        Attempts to match a street suffix. If found, it will return the abbreviation, with the first letter capitalized
        and a period after it. E.g. "St." or "Ave."
        """
        # Suffix must come before street
        if self.street_suffix is None and self.street is None:
            if token.upper() in self.parser.suffixes.keys():
                suffix = self.parser.suffixes[token.upper()]
                self.street_suffix = suffix.capitalize() + '.'
                return True
            elif token.upper() in self.parser.suffixes.values():
                self.street_suffix = token.capitalize() + '.'
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
            self.street = token.capitalize()
            return True
        # Now check for multiple word streets. This check must come after the check for street_prefix and house_number for this reason.
        elif self.street is not None and self.street_suffix is not None and self.street_prefix is None and self.house_number is None:
            self.street = token.capitalize() + ' ' + self.street
            return True
        if not self.street_suffix and not self.street and token.lower() in self.parser.streets:
            self.street = token
            return True
        return False

    def check_street_prefix(self, token):
        if self.street and not self.street_prefix and token.lower().replace('.', '') in self.parser.prefixes.keys():
            self.street_prefix = self.parser.prefixes[token.lower().replace('.', '')]
            return True
        return False

    def check_house_number(self, token):
        if self.street and self.house_number is None and re.match(street_num_regex, token.lower()):
            if '/' in token:
                token = token.split('/')[0]
            if '-' in token:
                token = token.split('-')[0]
            self.house_number = str(token)
            return True
        return False

    def check_building(self, token):
        # Building name check. If we have leftover and everything else is set, probably building names.
        # Allows for multiname buildings
        building_match = re.search(parentheses_buiding_regex, token)
        if building_match:
            self.building = building_match.group(0)
            address = re.subn(parentheses_buiding_regex, '', token)[0]

        if self.street and self.house_number:
            if not self.building:
                self.building = token
            else:
                self.building = token + ' ' + self.building
            return True
        return False

    def guess_unmatched(self, token):
        """
        When we find something that doesn't match, we can make an educated guess and log it as such.
        """
        # Let's check for a suffix-less street.
        if self.street_suffix is None and self.street is None and self.street_prefix is None and self.house_number is None:
            # Streets will just be letters
            if re.match(r"[A-Za-z]", token):
                print "Guessing suffix-less street: ", token
                self.street = token.capitalize()
                return True
        return False

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Address - House number: " + str(self.house_number) + " Prefix: " + str(self.street_prefix) + " Street: " + str(self.street) + " Suffix: " + str(self.street_suffix) + " Apartment: " + str(self.apartment) + " Building: " + str(self.building) + " City,State,Zip: " + str(self.city) + " " + str(self.state) + " " + str(self.zip)


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
