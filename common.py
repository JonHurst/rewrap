#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import tokenise

def dump_tokens(token_list, astext=False):
    outstr = ""
    if astext:
        outstr = u"".join([t[0] for t in token_list])
    else:
        for t in token_list:
            outstr += u"{%s}: %s\n" % (tokenise.token_description[t[1]], t[0])
    return outstr

