#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import tokenise

def dump_tokens(token_list, astext=False, outfh=sys.stdout):
    outstr = ""
    if astext:
        for t in token_list:
            outstr += t[0]
    else:
        for t in token_list:
            outstr += "{%s}: %s\n" % (tokenise.token_description[t[1]], t[0])
    outfh.write(outstr.encode("utf-8") + "\n")

