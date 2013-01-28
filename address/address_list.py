from __future__ import division
import sys
import os
from address import Address, AddressParser


if __name__ == '__main__':
    # The mini test program takes a list of addresses, creates Address objects, and prints errors for each one
    # with unmatched terms. Takes a filename as the first and only argument. The file should be one address per line.
    if len(sys.argv) != 2:
        print "Usage: test_list.py filename"
        sys.exit(1)
    if not os.path.exists(sys.argv[1]):
        print "File {0} does not exist".format(sys.argv[1])
        sys.exit(2)
    unmatched_count = 0
    line_count = 0
    ap = AddressParser()
    with open(sys.argv[1]) as input:
        for line in input:
            addr = ap.parse_address(line.strip(), line_number=line_count)

            if addr.unmatched:
                print "Unmatched", addr, addr.line_number
                print ""
                unmatched_count = unmatched_count + 1
            # All addresses have a house number and a street.
            if addr.house_number is None:
                print "House number cannot be None: ", addr, addr.line_number
            if addr.street is None:
                print "Street cannot be None: ", addr, addr.line_number
            line_count = line_count + 1
            print addr.full_address()
            print addr.original
            print ""
    if unmatched_count == 0:
        print "All {0} address matched! Huzzah!".format(line_count)
    else:
        print "{0} addresses of {1} ({2:.2%}) with unmatched terms. :(".format(unmatched_count, line_count, unmatched_count / line_count)
