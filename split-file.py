#!/usr/bin/python

#!/usr/bin/python

import sys
import re

#usage split_file file

if len(sys.argv) != 2:
    print "Usage: ", sys.argv[0], "filename"
    sys.exit()
regexp = re.compile("""=====#(\d+)#=====""")
outstr = ""
for line in file(sys.argv[1]):
    mo = regexp.match(line)
    if mo:
        outfile = open(mo.group(1), "w")
        outfile.write(outstr)
        outfile.close()
        outstr = ""
    else:
        outstr += line


