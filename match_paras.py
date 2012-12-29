#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The purpose of match_para is to take two files consisting of a template file and an input file and
output a file that has the same paragraph structure as the template file but as much content as
possible from the input file.

Matching of paragraphs is achieved by comparing paragraph signatures. A signature is a set
consisting of the paragraph's words converted to lowercase plus any digits it may contain. Thus the
signature is unaffected by differences in spacing, punctuation, line breaking or capitalisation.

The process is to first find exactly matching signatures and use these to break the files into
subsections. Matching subsections are then compared more closely to find paragraphs that are near
matches. The global variable match_criteria defines what is "close enough" to be considered a near
match.

An attempt is also made to deal with paragraphs that have either been split or joined. There are
many corner cases in this aspect, so only those cases that can be processed with reasonable
certainty are automated and warnings are generated for those where manual intervention will be
required. In general, joining appears to be relatively robust but splitting often proves tricky.
"""

import tokenise
import sys
import difflib
import math
import glob
import os.path
from common import dump_tokens, linebreak_to_space
import wrap


match_criteria = 0.85


def sig(tokens):
    """Makes a signature for a list of tokens by creating a frozen set consisting of all the words
    lower-cased. This makes signatures quite robust across many of the normal edition differences
    such as punctuation changes and case changes."""
    t_applicable = [t for t in tokens if t[1] & (tokenise.TYPE_WORD | tokenise.TYPE_DIGIT)]
    if not t_applicable:
        return frozenset()
    else:
        return frozenset([t[0].lower() for t in t_applicable])


def split_and_sign_paras(tokens):
    """Split a list of tokens into a list of signed paragraphs of the form:
    [[sig1, tok1.1, tok1.2...], [sig2, tok2.1, tok2.2, ...], ...]"""
    unsigned_paras = wrap.split_paras(tokens)
    signed_paras = []
    for p in unsigned_paras:
        signed_paras.append([sig(p)] + p)
    return signed_paras


def make_para_dict(para_list):
    """Take a signed para_list (as output by split_and_sign_paras) and create a dictionary with the
    para's sig as key and the indexes of matching paras as value in the form [index1, ...]. The
    indexes will be in document order."""
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
    matching indexes of the form [[ind, ind], [ind, ind], ...]."""
    para_dict = make_para_dict(para_list_2)
    para_match_list = []
    for c, p in enumerate(para_list_1):
        if para_dict.has_key(p[0]) and para_dict[p[0]]:
            d = para_dict[p[0]][0]
            para_match_list.append([c, d, (1.0, 1.0)])
            del para_dict[p[0]][0]
    return para_match_list


def fuzzy_match_p(t_sig, i_sig):
    """Predicate function for determining whether two paragraphs probabalistically match. Returns
    False if it is unlikely that they match. Returns a tuple pair of the form:
       (template_match_probability, input_match_probability)
    if one signature is a near subset of the other."""
    intersection = t_sig & i_sig
    max_intersection_len = min(len(t_sig), len(i_sig))
    #match criteria is global set at the top of this file
    if float(len(intersection))/max_intersection_len < match_criteria : return False
    t_match = float(len(intersection)) / len(t_sig)
    i_match = float(len(intersection)) / len(i_sig)
    return (t_match, i_match)


def fuzzy_match_paras(t_paras, i_paras):
    """Find matches in the t_paras list and i_paras list. The sigs in these lists may be None if an
    exact matches have already been made. Returns a list of matches of the form:
      [[[t_para_index, ...], [i_para_index, ...], (t_match_prob, i_match_prob)], ...].
    Multiple t_para_indexes indicate the input paragraph requires splitting, multiple i_para_indexes
    indicates the input paragraph requires joining."""
    match_list = []
    for ct, pt in enumerate(t_paras):
        if not pt[0]: continue
        for ci, pi in enumerate(i_paras):
            if not pi[0]: continue
            match_probs = fuzzy_match_p(pt[0], pi[0])
            if match_probs:
                match_list.append([[ct], [ci], match_probs])
    #process joins and splits
    def build_candidate(paras, index_list):
        candidate = []
        for i in index_list:
            candidate.append(paras[i])
        return join_paras(candidate)
    c = 0
    while c + 1 < len(match_list):
        #detect and process join case
        if (match_list[c][0][-1] == match_list[c + 1][0][0] and
            match_list[c][1][-1] + 1 == match_list[c + 1][1][0]):
            t_candidate = build_candidate(t_paras, match_list[c][0])
            i_candidate = build_candidate(i_paras, match_list[c][1] + match_list[c + 1][1])
            match_probs = fuzzy_match_p(t_candidate[0], i_candidate[0])
            if match_probs and sum(match_probs[:2]) > sum(match_list[c][2][:2]):
                match_list[c + 1] = [match_list[c][0], match_list[c][1] + match_list[c + 1][1], match_probs]
                match_list[c] = None
        #detect and process split case
        elif (match_list[c][0][-1] + 1 == match_list[c + 1][0][0] and
            match_list[c][1][-1]  == match_list[c + 1][1][0]):
            t_candidate = build_candidate(t_paras, match_list[c][0] + match_list[c + 1][0])
            i_candidate = build_candidate(i_paras, match_list[c][1])
            match_probs = fuzzy_match_p(t_candidate[0], i_candidate[0])
            if match_probs and sum(match_probs[:2]) > sum(match_list[c][2][:2]):
                match_list[c + 1] = [match_list[c][0] + match_list[c + 1][0], match_list[c][1], match_probs]
                match_list[c] = None
        c += 1
    #now drop anything where either criteria is below match criteria:
    for c, m in enumerate(match_list):
        if m and (min(*m[2]) < match_criteria):
            match_list[c] = None
    return match_list


def join_paras(para_list):
    """Turns para_list into a single para"""
    para = []
    for p in para_list:
        para += p[1:]
    para.insert(0, sig(para))
    return para


def break_para(t_paras, i_para, logger):
    """Breaks i_para into a list of paras that approximately match those in the t_paras list"""
    #normalise t_paras
    t_tokens = join_paras(t_paras)[1:]
    linebreak_to_space(t_tokens)
    #normalise i_para
    i_tokens = i_para[1:]
    i_oldtokens = i_tokens[:]
    linebreak_to_space(i_tokens)
    #insert parabreak tokens into t_tokens
    c = 0
    for p in t_paras:
        c += len(p) - 1
        assert t_tokens[c - 1][1] & tokenise.TYPE_SPACE
        t_tokens[c - 1] = ["\n", tokenise.TYPE_LINEBREAK | tokenise.TYPE_PARABREAK]
    #wrap i_tokens using t_tokens
    i_tokens = wrap.wrap_para(t_tokens, i_tokens, logger)
    #copy old linebreaks back into i_tokens
    for c, t in enumerate(i_oldtokens):
        if (t[1] & tokenise.TYPE_LINEBREAK) and (i_tokens[c][1] & tokenise.TYPE_SPACE):
            i_tokens[c] = t
    return split_and_sign_paras(i_tokens)



def process_matches(matches, t_para_list, i_para_list, logger):
    """Processes the joins and splits indicated by a match list of the form output by
    build_match_list into a simpler form where each index list contains only one index, i.e. it
    produces a 1-to-1 mapping of template paragraphs to input paragraphs. Split and joined
    paragraphs are appended to i_para_list as necessary."""
    #modify i_para_list and matches for joins
    for c, m in enumerate(matches):
        if len(m[1]) > 1:
            joined_para = []
            logger.set_current_para(m[0][0], m[1][0])
            logger.message("Info: Joining input paras %s" % (
                    ", ".join(["%04d" % X for X in m[1]])))
            for ci in m[1]:
                joined_para += i_para_list[ci][1:-1] + [["\n", tokenise.TYPE_LINEBREAK]]
            joined_para.insert(0, sig(joined_para))
            i_para_list.append(joined_para)
            matches[c][1] = [len(i_para_list) - 1]
    #modify i_para_list and matches for splits
    new_matches = []
    for c, m in enumerate(matches):
        if len(m[0]) > 1:
            t_paras = []
            logger.set_current_para(m[0][0], m[1][0])
            logger.message("Info: Splitting input para (template paras %s)]" % (
                    ", ".join(["%04d" % X for X in m[0]])))
            for i in m[0]:
                t_paras.append(t_para_list[i])
            split_paras = break_para(t_paras, i_para_list[m[1][0]], logger)
            for d, i in enumerate(m[0]):
                if d >= len(split_paras): break
                i_para_list.append(split_paras[d])
                match_prob = fuzzy_match_p(t_para_list[i][0], split_paras[d][0])
                if match_prob and min(*match_prob) >= match_criteria:
                    new_matches.append([[i], [len(i_para_list) - 1], match_prob])
            matches[c] = None
    matches += new_matches
    matches = [X for X in matches if X]
    matches.sort()
    return matches


def build_match_list(t_para_list, i_para_list):
    """Takes two lists of paragraphs and calculates a match list of the form:
      [[[t_para_index, ...], [i_para_index, ...], (t_match_prob, i_match_prob)], ...]"""
    exact_matches = match_paras(t_para_list, i_para_list)
    matches = []
    for start, end in zip([[-1, -1]] + exact_matches,
                          exact_matches + [[len(t_para_list), len(i_para_list)]]):
        matches.append([[X] for  X in start])
        start = [X + 1 for X in start[:2]]
        if end[0] <= start[0] or end[1] <= start[1]: continue
        t_fuzzy = t_para_list[start[0]:end[0]]
        i_fuzzy = i_para_list[start[1]:end[1]]
        fuzzy_matches = fuzzy_match_paras(t_fuzzy, i_fuzzy)
        for fm in fuzzy_matches:
            if not fm: continue
            fm[0] = [X + start[0] for X in fm[0]]
            fm[1] = [X + start[1] for X in fm[1]]
            matches.append(fm)
    del matches[0]
    return matches


def build_output(t_para_list, i_para_list, matches, logger):
    """Takes the simplified match list produced by process_matches plus the template paragraph list
    and modified input paragraph list and builds an output string. Where a match exists between a
    template paragraph and an input paragraph, the input paragraph is output; otherwise the template
    paragraph is retained and a warning issued. This function also calculates the usage rates of
    template and input tokens."""
    outdict = {}
    for m in matches:
        if not outdict.has_key(m[0][0]):#chooses first match if multiples
            outdict[m[0][0]] = m[1][0]
    outstrings = []
    def add_output_para(tokens):
        outstrings.append("".join([X[0] for X in tokens]))
    t_count, i_count = 0, 0
    for c in range(0, len(t_para_list)):
        desc = str(c)
        if outdict.has_key(c):
            add_output_para(i_para_list[outdict[c]][1:])
            i_count += len(i_para_list[outdict[c]][1:])
        else:
            logger.set_current_para(c)
            logger.message("Warning: Retaining template para")
            add_output_para(t_para_list[c][1:])
            t_count += len(t_para_list[c][1:])
    print "t_count:", t_count, "i_count:", i_count, "rep_rate:", str(i_count * 100 / (t_count + i_count)) + "%"
    return "\n".join(outstrings)


def main():
    """Loads the template and input files and processes them into an output file. The output file
    will have the same name as the input file with ".paramatch" appended."""
    if len(sys.argv) != 3 or not os.path.isfile(sys.argv[1]) or not os.path.isfile(sys.argv[2]):
        print "Usage: %s template_file input_file" % sys.argv[0]
        sys.exit(-1)
    #process template file(s) into para list
    t_string = unicode(file(sys.argv[1]).read(), "utf-8")
    t_tokens = tokenise.tokenise(t_string)
    t_para_list = split_and_sign_paras(t_tokens)
    #process input file into para list
    i_string = unicode(file(sys.argv[2]).read(), "utf-8")
    i_tokens = tokenise.tokenise(i_string)
    i_para_list = split_and_sign_paras(i_tokens)
    #process token lists
    logger = wrap.Logger(t_string, i_string)
    matches = build_match_list(t_para_list, i_para_list)
    matches = process_matches(matches, t_para_list, i_para_list, logger)
    # for m in matches:
    #     print "%04d = %04d : %3d%%" % (m[0][0], m[1][0], int(math.ceil(min(*m[2]) * 100)))
    output = build_output(t_para_list, i_para_list, matches, logger)
    file(sys.argv[2] + ".paramatch", "w").write(output.encode("utf-8"))


if __name__ == "__main__":
    main()
