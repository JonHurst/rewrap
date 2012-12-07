#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This program takes a template file and an input file, and outputs
the input file with the page breaks and line breaks from the template
file.

The program assumes that the paragraphs in the template file and input
file are in corresponding positions. Use the match_para program to
acheive this if necessary."""

import sys
import os
import tokenise
import filters
from common import split_paras, dump_tokens, sig


def build_match_list(t_tokens, i_tokens):
    matches = []
    i_token_dict = {}
    for c, t in enumerate(i_tokens):
        if t[1] in (tokenise.TYPE_WORD, tokenise.TYPE_DIGIT):
            key = t[0].lower()
            if i_token_dict.has_key(key):
                i_token_dict[key] = None
            else:
                i_token_dict[key] = c
    for c, t in enumerate(t_tokens):
        if t[1] in (tokenise.TYPE_WORD, tokenise.TYPE_DIGIT):
            key = t[0].lower()
            if i_token_dict.has_key(key) and i_token_dict[key] != None:
                matches.append([c, i_token_dict[key]])
    c = 1
    while c < len(matches):
        if matches[c][1] < matches[c - 1][1]:
            del matches[c]
        else:
            c += 1
    return matches


def merge_breaks(t_shard, i_shard):
    if len(t_shard) == len(i_shard):
        for c, t in enumerate(t_shard):
            if (t[1] == tokenise.TYPE_LINEBREAK
                and i_shard[c][1] == tokenise.TYPE_SPACE):
                i_shard[c] = t
    return i_shard


def wrap_para(t_para, i_para):
    t_tokens, i_tokens = t_para[1:], i_para[1:]
    o_tokens = []
    filters.linebreak_to_space(i_tokens)
    matches = build_match_list(t_tokens, i_tokens)
    #handle shards before first match
    t_shard = t_tokens[:matches[0][0]]
    if t_shard:
        i_shard = i_tokens[0:matches[0][1]]
        o_tokens = merge_breaks(t_shard, i_shard)
    for start, end in zip(matches, matches[1:] + [[len(t_tokens), len(i_tokens)]]):
        o_tokens.append(i_tokens[start[1]])
        t_shard = t_tokens[start[0] + 1:end[0]]
        if t_shard:
            i_shard = i_tokens[start[1] + 1:end[1]]
            o_tokens += merge_breaks(t_shard, i_shard)
    o_tokens.insert(0, sig(o_tokens))
    return o_tokens


def main():
    if len(sys.argv) != 3 or not os.path.isfile(sys.argv[1]) or not os.path.isfile(sys.argv[2]):
        print "Usage: %s template_file input_file" % sys.argv[0]
        sys.exit(-1)
    #process template file(s) into para list
    t_tokens = tokenise.tokenise(unicode(file(sys.argv[1]).read(), "utf-8"))
    t_para_list = split_paras(t_tokens)
    #process input file into para list
    i_tokens = tokenise.tokenise(unicode(file(sys.argv[2]).read(), "utf-8"))
    i_para_list = split_paras(i_tokens)
    wrapped_paras = []
    for t_para, i_para in zip(t_para_list, i_para_list)[10:20]:
        if t_para != i_para:
            wrapped_paras.append(wrap_para(t_para, i_para))
        else:
            wrapped_paras.append(i_para)
    for p in wrapped_paras:
        if not p: continue
        print dump_tokens(p[1:], True).encode("utf-8")


if __name__ == "__main__":
    main()
