#!/usr/bin/python

import sys
import re

text = unicode(sys.stdin.read(), "utf-8")
paras = re.split(r"\n\n+", text)
for c, p in enumerate(paras):
    p = (ur"\\%04d\\" % c) + p + u"\n\n"
    sys.stdout.write(p.encode("utf-8"))
