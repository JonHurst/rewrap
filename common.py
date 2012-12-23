#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import tokenise

def dump_tokens(token_list, astext=False):
    outstr = ""
    if astext:
        for t in token_list:
            outstr += t[0]
            if (t[1] & tokenise.TYPE_PAGEBREAK) and len(t) == 3:
                outstr += u"=====#%s#=====\n" % t[2]
    else:
        for t in token_list:
            k = [X for X in tokenise.token_description.keys() if (t[1] & X)]
            outstr += u"{%s}: %s\n" % (
                str([tokenise.token_description[X] for X in k]), t[0])
    return outstr


def linebreak_to_space(tokens):
    for c, t in enumerate(tokens):
        if t[1] & tokenise.TYPE_LINEBREAK:
            tokens[c] = [" ", tokenise.TYPE_SPACE]
