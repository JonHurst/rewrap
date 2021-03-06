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
import glob
import tokenise
from common import dump_tokens, linebreak_to_space

class Logger:

    def __init__(self, template_string, input_string):
        self.template_para = None
        self.input_para = None
        self.template_line_dict = self.__build_line_dict(template_string)
        self.input_line_dict = self.__build_line_dict(input_string)


    def __build_line_dict(self, s):
        d = {}
        in_para = False
        para_count = 0
        for c, l in enumerate(s.splitlines()):
            if len(l.rstrip()):
                if not in_para:
                    in_para = True
                    d[para_count] = c + 1
                    para_count += 1
            else:
                in_para = False
        return d


    def set_current_para(self, template_para, input_para=None):
        self.template_para = template_para
        self.input_para = input_para


    def message(self, s, t_shard=None, i_shard=None):
        t_para_str = ""
        if self.template_para != None:
            t_para_str = " t:%04d(%05d)" % (
                self.template_para, self.template_line_dict.get(self.template_para, 99999))
        i_para_str = ""
        if self.input_para != None :
            i_para_str = " i:%04d(%05d)" % (
                self.input_para, self.input_line_dict.get(self.input_para, 99999))
        print "[", s + t_para_str + i_para_str, "]"
        if t_shard:
            print "    t:", dump_tokens(t_shard, True).encode("utf-8").replace("\n", "¶")
        if i_shard:
            print "    i:", dump_tokens(i_shard, True).encode("utf-8").replace("\n", "¶")


def split_paras(tokens):
    """Split a list of tokens into a list of paragraphs of the form:
    [[tok1.1, tok1.2...], [tok2.1, tok2.2, ...], ...]"""
    para_list = []
    para = []
    for t in tokens:
        para.append(t)
        if t[1] & tokenise.TYPE_PARABREAK:
            para_list.append(para)
            para = []
    if para:
        para_list.append(para)
    return para_list


def token_dict(tokens):
    token_dict = {}
    for c, t in enumerate(tokens):
        if t[1] & (tokenise.TYPE_WORD | tokenise.TYPE_DIGIT):
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
        if t_token_dict.get(key) != None and i_token_dict.get(key) != None:
            matches.append([c, i_token_dict[key]])
    #ensure matches monotonically increases in both fields
    c = 1
    while c < len(matches):
        #simple test
        if matches[c][1] < matches[c - 1][1]: break
        c += 1
    if c != len(matches):
        #failed test - do removal
        matches_copy = matches[:]
        matches_copy.sort(lambda x,y: x[1] - y[1])
        c = 0
        while c < len(matches):
            if matches[c] != matches_copy[c]:
                del matches[matches.index(matches_copy[c])]
                del matches_copy[matches_copy.index(matches[c])]
                del matches[c]
                del matches_copy[c]
            else:
                c += 1
    return matches


def merge_breaks(t_shard, i_shard, logger):
    #if there are no line breaks in the shard, just return the i_shard
    if not [X for X in t_shard if X[1] & tokenise.TYPE_LINEBREAK]:
        return i_shard
    #so, there are some linebreaks...
    nt_shard = t_shard[:]
    linebreak_to_space(nt_shard)
    if i_shard == nt_shard:
        #simple case -- identical shards if you replace the linebreaks with spaces
        for c, t in enumerate(t_shard):
            if t[1] & tokenise.TYPE_LINEBREAK:
                i_shard[c] = t
    else:
        #bring in the big guns!
        nt_seq = tuple([tuple(X) for X in nt_shard])
        i_seq = tuple([tuple(X) for X in i_shard])
        sm = difflib.SequenceMatcher(None, nt_seq, i_seq, False)
        mb = sm.get_matching_blocks()
        if len(mb) == 1:
            #no match in shards
            logger.message("Warning: No matches", t_shard, i_shard)
            return i_shard
        for ct, t in enumerate(t_shard):
            if t[1] & tokenise.TYPE_LINEBREAK:
                #find the match block after the linebreak
                for cm, m in enumerate(mb):
                    if m[0] > ct: break
                if cm == 0:
                    if ct == 0 and (i_shard[0][1] & tokenise.TYPE_SPACE):
                        i_shard[0] = t
                    else:
                        logger.message("Warning: No candidate space", t_shard, i_shard)
                elif mb[cm - 1][0] + mb[cm - 1][2] > ct:
                    #break occured inside prev matchblock
                    i_shard[ct + mb[cm - 1][1] - mb[cm - 1][0]] = t
                elif mb[cm][0] - 1 == ct:
                    #break occurred just prior to matchblock
                    candidate = mb[cm][1] - 1
                    if i_shard[candidate][1] & tokenise.TYPE_SPACE:
                        i_shard[candidate] = t
                    elif i_shard[candidate][0] == "-":
                        #line is broken at hyphen
                        i_shard[candidate] = t
                        i_shard[candidate][0] = "-" + i_shard[candidate][0]
                    else:
                        logger.message("Warning: No candidate space", t_shard, i_shard)
                else:
                    #match occurred outside matchblock
                    logger.message("Warning: Break outside match block", t_shard, i_shard)
    return i_shard


def wrap_para(t_para, i_para, logger):
    t_tokens, i_tokens = t_para[:], i_para[:]
    o_tokens = []
    linebreak_to_space(i_tokens)
    matches = build_match_list(t_tokens, i_tokens)
    #handle shards before first match
    if not matches: return i_para
    t_shard = t_tokens[:matches[0][0]]
    i_shard = i_tokens[:matches[0][1]]
    if t_shard or i_shard:
        i_shard = i_tokens[0:matches[0][1]]
        o_tokens = merge_breaks(t_shard, i_shard, logger)
    for start, end in zip(matches, matches[1:] + [[len(t_tokens), len(i_tokens)]]):
        o_tokens.append(i_tokens[start[1]])
        t_shard = t_tokens[start[0] + 1:end[0]]
        if t_shard:
            i_shard = i_tokens[start[1] + 1:end[1]]
            o_tokens += merge_breaks(t_shard, i_shard, logger)
    if o_tokens[-1][1] & tokenise.TYPE_SPACE:
        logger.message("Warning: Additional material after final linebreak", t_shard, i_shard)
        o_tokens[-1] = ("\n", tokenise.TYPE_LINEBREAK | tokenise.TYPE_PARABREAK)
    return o_tokens


def build_output(wrapped_paras):
    outstrings = []
    for p in wrapped_paras:
        if not p: continue
        outstrings.append("")
        for t in p:
            outstrings[-1] += t[0]
            if (t[1] & tokenise.TYPE_PAGEBREAK) and len(t) == 3:
                outstrings[-1] += u"=====#%s#=====\n" % t[2]
    return "\n".join(outstrings)


def main():
    if len(sys.argv) != 3 or not os.path.isfile(sys.argv[1]) or not os.path.isfile(sys.argv[2]):
        print "Usage: %s template_file input_file" % sys.argv[0]
        sys.exit(-1)
    #process template file(s) into para list
    t_string = unicode(file(sys.argv[1]).read(), "utf-8")
    t_tokens = tokenise.tokenise(t_string)
    t_para_list = split_paras(t_tokens)
    #process input file into para list
    i_string = unicode(file(sys.argv[2]).read(), "utf-8")
    i_tokens = tokenise.tokenise(i_string)
    i_para_list = split_paras(i_tokens)
    #sanity check -- must be the same number of paras in template and input
    if len(t_para_list) != len(i_para_list):
        print "Number of paragraphs\n template: %s\n input: %s" % (
            len(t_para_list), len(i_para_list))
        sys.exit(-2)
    #initialise logger
    logger = Logger(t_string, i_string)
    wrapped_paras = []
    for c, (t_para, i_para) in enumerate(zip(t_para_list, i_para_list)):
        logger.set_current_para(c, c)
        if t_para != i_para:
            wrapped_paras.append(wrap_para(t_para, i_para, logger))
        else:
            wrapped_paras.append(i_para)
    outfile = open(sys.argv[2] + ".wrap", "w")
    outfile.write(build_output(wrapped_paras).encode("utf-8"))


if __name__ == "__main__":
    main()
