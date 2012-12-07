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


def split_paras(tokens):
    """Split a list of tokens into a list of paragraphs of the form:
    [[sig1, tok1.1, tok1.2...], [sig2, tok2.1, tok2.2, ...], ...]"""
    if tokens[0][1] == tokenise.TYPE_LINEBREAK:
        tokens[0][1] = tokenise.TYPE_PARABREAK
    para_list = []
    para = []
    name = ""
    for t in tokens:
        if t[1] == tokenise.TYPE_PARABREAK:
            para.insert(0, sig(para))
            para_list.append(para)
            para = []
        else:
            para.append(t)
    if para:
        para.insert(0, sig(para))
        para_list.append(para)
    return para_list


def sig(tokens):
    """Makes a signature for a list of tokens by creating a frozen set consisting of all the words
    lower-cased. This makes signatures quite robust across many of the normal edition differences
    such as punctuation changes and case changes."""
    t_applicable = [t for t in tokens if t[1] == tokenise.TYPE_WORD or t[1] == tokenise.TYPE_DIGIT]
    if not t_applicable:
        return frozenset()
    else:
        return frozenset([t[0].lower() for t in t_applicable])


