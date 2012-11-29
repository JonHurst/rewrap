#!/usr/bin/python
# -*- coding: utf-8 -*-

import tokenise
import sys
import common

template_file = "template"
input_file = "input"


def sig(tokens):
    """Makes a signature for a list of tokens by creating a frozen set consisting of all the words
    lower-cased. This makes signatures quite robust across many of the normal edition differences
    such as punctuation changes and case changes."""
    return frozenset([t[0].lower() for t in tokens if t[1] == tokenise.TYPE_WORD])


def split_paras(tokens):
    """Split a list of tokens into a list of paragraphs of the form:
    [[sig1, tok1.1, tok1.2...], [sig2, tok2.1, tok2.2, ...], ...]"""
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
    return para_list


def make_para_dict(para_list):
    """Take a para_list (as output by split_paras) and create a dictionary with the para's sig as
    key and the indexes of matching paras as value in the form [index1, ...]. The indexes will be in
    document order."""
    para_dict = {}
    for c, para_desc in enumerate(para_list):
        key = para_desc[0]
        if para_dict.has_key(key):
            para_dict[key].append(c)
        else:
            para_dict[key] = [c]
    return para_dict


def match_paras(para_list_1, para_list_2):
    """Find "exact" matches where sigs are equal in para_list_1 and para_list_2. Returns a list of
    matching indexes of the form [[ind, ind], [ind, ind], ...]"""
    para_dict = make_para_dict(para_list_2)
    para_match_list = []
    for c, p in enumerate(para_list_1):
        if para_dict.has_key(p[0]) and para_dict[p[0]]:
            para_match_list.append([c, para_dict[p[0]][0]])
            del para_dict[p[0]][0]
    return para_match_list


def main():
    #process input file into para list
    i_tokens = tokenise.tokenise(file(input_file).read())
    i_para_list = split_paras(i_tokens)
    #process token file into para list
    t_tokens = tokenise.tokenise(file(template_file).read())
    t_para_list = split_paras(t_tokens)
    #find exact matches
    exact_matches = match_paras(t_para_list, i_para_list)
    print exact_matches

main()
