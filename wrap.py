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
import difflib
import tokenise
import filters
from common import split_paras, dump_tokens, sig

current_para = 0

def set_current_para(d):
    global current_para
    current_para = d

def warning(s, t_shard=None, i_shard=None):
    print "[%04d Warning: %s]" % (current_para, s)
    if t_shard:
        print "    t:", dump_tokens(t_shard, True).encode("utf-8").replace("\n", "¶")
    if i_shard:
        print "    i:", dump_tokens(i_shard, True).encode("utf-8").replace("\n", "¶")


def token_dict(tokens):
    token_dict = {}
    for c, t in enumerate(tokens):
        if t[1] in (tokenise.TYPE_WORD, tokenise.TYPE_DIGIT):
            key = t[0].lower()
            if token_dict.has_key(key):
                token_dict[key] = None
            else:
                token_dict[key] = c
    return token_dict


def build_match_list(t_tokens, i_tokens):
    matches = []
    t_token_dict = token_dict(t_tokens)
    i_token_dict = token_dict(i_tokens)
    for c, t in enumerate(t_tokens):
        key = t[0].lower()
        if t_token_dict.get(key) and i_token_dict.get(key):
            matches.append([c, i_token_dict[key]])
    #ensure matches monotonically increases in both fields
    #TODO: this needs improving
    c = 1
    while c < len(matches):
        if matches[c][1] < matches[c - 1][1]:
            del matches[c]
            warning("Bad word match: %s" % t_tokens[matches[c][1]][0])
        else:
            c += 1
    return matches


def merge_breaks(t_shard, i_shard):
    #if there are no line breaks in the shard, just return the i_shard
    if tokenise.TYPE_LINEBREAK not in [X[1] for X in t_shard]:
        return i_shard
    #so, there are some linebreaks...
    nt_shard = t_shard[:]
    filters.linebreak_to_space(nt_shard)
    if i_shard == nt_shard:
        #simple case -- identical shards if you replace the linebreaks with spaces
        for c, t in enumerate(t_shard):
            if t[1] == tokenise.TYPE_LINEBREAK:
                i_shard[c] = t
    else:
        #bring in the big guns!
        nt_seq = tuple([tuple(X) for X in nt_shard])
        i_seq = tuple([tuple(X) for X in i_shard])
        sm = difflib.SequenceMatcher(None, nt_seq, i_seq, False)
        mb = sm.get_matching_blocks()
        if len(mb) == 1:
            #no match in shards
            warning("No matches", t_shard, i_shard)
            return i_shard
        for ct, t in enumerate(t_shard):
            if t[1] == tokenise.TYPE_LINEBREAK:
                #find the match block after the linebreak
                for cm, m in enumerate(mb):
                    if m[0] > ct: break
                if cm == 0:
                    if ct == 0 and i_shard[0][1] == tokenise.TYPE_SPACE:
                        i_shard[0] = t
                    else:
                        warning("No candidate space", t_shard, i_shard)
                elif mb[cm - 1][0] + mb[cm - 1][2] > ct:
                    #break occured inside prev matchblock
                    i_shard[ct + mb[cm - 1][1] - mb[cm - 1][0]] = t
                elif mb[cm][0] - 1 == ct:
                    #break occurred just prior to matchblock
                    candidate = mb[cm][1] - 1
                    if i_shard[candidate][1] == tokenise.TYPE_SPACE:
                        i_shard[candidate] = t
                    else:
                        warning("No candidate space", t_shard, i_shard)
                else:
                    #match occurred outside matchblock
                    warning("Break outside match block", t_shard, i_shard)
    return i_shard


def wrap_para(t_para, i_para):
    t_tokens, i_tokens = t_para[1:], i_para[1:]
    o_tokens = []
    filters.linebreak_to_space(i_tokens)
    matches = build_match_list(t_tokens, i_tokens)
    #handle shards before first match
    if not matches: return i_para
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
    if o_tokens[-1][1] == tokenise.TYPE_SPACE:
        warning("Additional material after final linebreak", t_shard, i_shard)
        o_tokens[-1] = ("\n", tokenise.TYPE_LINEBREAK)
    o_tokens.insert(0, sig(o_tokens))
    return o_tokens


def main():
    global current_para
    if len(sys.argv) != 3 or not os.path.isfile(sys.argv[1]) or not os.path.isfile(sys.argv[2]):
        print "Usage: %s template_file input_file" % sys.argv[0]
        sys.exit(-1)
    #process template file(s) into para list
    t_tokens = tokenise.tokenise(unicode(file(sys.argv[1]).read(), "utf-8"))
    t_para_list = split_paras(t_tokens)
    #process input file into para list
    i_tokens = tokenise.tokenise(unicode(file(sys.argv[2]).read(), "utf-8"))
    i_para_list = split_paras(i_tokens)
    if len(t_para_list) != len(i_para_list):
        print "Number of paragraph template and input differ"
        sys.exit(-2)
    wrapped_paras = []
    for c, (t_para, i_para) in enumerate(zip(t_para_list, i_para_list)):
        set_current_para(c)
        if t_para != i_para:
            wrapped_paras.append(wrap_para(t_para, i_para))
        else:
            wrapped_paras.append(i_para)
    outfile = open(sys.argv[2] + ".wrap", "w")
    for p in wrapped_paras:
        if not p: continue
        outfile.write(dump_tokens(p[1:], True).encode("utf-8") + "\n")


if __name__ == "__main__":
    main()