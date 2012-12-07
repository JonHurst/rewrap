#!/usr/bin/python

import sys

text = unicode(sys.stdin.read(), "utf-8")
c = 0
if text[0] == u"\n":
    sys.stdout.write(u"\\\\0000\\\\\n")
    c = 1
    text = text[1:]
paras = text.split(u"\n\n")
for p in paras:
    p = (ur"\\%04d\\" % c) + p + u"\n\n"
    sys.stdout.write(p.encode("utf-8"))
    c += 1
