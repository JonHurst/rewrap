#!/usr/bin/python
# -*- coding: utf-8 -*-

import tokenise

def dump_tokens(token_list, astext=False):
    if astext:
        outstr = ""
        for t in token_list:
            outstr += t[0]
        print outstr
    else:
        for t in token_list:
            print "{", tokenise.token_description[t[1]], "}:", t[0]


