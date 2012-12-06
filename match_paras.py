#!/usr/bin/python
# -*- coding: utf-8 -*-

import tokenise
import sys
import common
import difflib
import filters
import math

template_file = "template"
input_file = "input"


def sig(tokens):
    """Makes a signature for a list of tokens by creating a frozen set consisting of all the words
    lower-cased. This makes signatures quite robust across many of the normal edition differences
    such as punctuation changes and case changes."""
    t_applicable = [t for t in tokens if t[1] == tokenise.TYPE_WORD or t[1] == tokenise.TYPE_DIGIT]
    if not t_applicable:
        return frozenset()
    else:
        return frozenset([t[0].lower() for t in t_applicable])


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
    matching indexes of the form [[ind, ind], [ind, ind], ...]. As a side-effect, the sigs for
    the matched paras in the two lists are set to None."""
    para_dict = make_para_dict(para_list_2)
    para_match_list = []
    for c, p in enumerate(para_list_1):
        if para_dict.has_key(p[0]) and para_dict[p[0]]:
            d = para_dict[p[0]][0]
            para_match_list.append([c, d])
            del para_dict[p[0]][0]
            para_list_1[c][0] = None
            para_list_2[d][0] = None
    return para_match_list


def fuzzy_match_p(t_sig, i_sig):
    intersection = t_sig & i_sig
    max_intersection_len = min(len(t_sig), len(i_sig))
    #match criteria is 90% of words the same or no more than 1 word wrong,
    #whichever is lower, excepting the case when there are less than two words
    if max_intersection_len > 1:
        match_criteria = 1 - (float(1) / max_intersection_len)
    else:
        match_criteria = 0.5
    match_criteria = min(match_criteria, 0.85)
    if float(len(intersection))/max_intersection_len < match_criteria :
        #somewhat certain there is no match
        return False
    t_match = float(len(intersection)) / len(t_sig)
    i_match = float(len(intersection)) / len(i_sig)
    return (t_match, i_match, match_criteria)


def build_candidate(paras, index_list):
    candidate = []
    for i in index_list:
        candidate.append(paras[i])
    return join_paras(candidate)


def fuzzy_match_paras(t_paras, i_paras):
    """Find matches in the t_paras list and i_paras list. The sigs in these lists may be None if an
    exact matches have already been made."""
    match_list = []
    for ct, pt in enumerate(t_paras):
        if not pt[0]: continue
        for ci, pi in enumerate(i_paras):
            if not pi[0]: continue
            match_probs = fuzzy_match_p(pt[0], pi[0])
            if match_probs:
                match_list.append([[ct], [ci], match_probs])
    #process joins and splits
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
        if m and (m[2][0] < m[2][2] or m[2][1] < m[2][2]):
            match_list[c] = None
    return match_list


def join_paras(para_list):
    """Turns para_list into a single para"""
    para = []
    for p in para_list:
        para += p[1:]
    para.insert(0, sig(para))
    return para


def break_para(t_paras, i_para):
    """Breaks i_para into a list of paras that approximately match those in the t_paras list"""
    if len(t_paras) == 1: return [i_para] #recursive terminator
    l_para = t_paras[0]
    r_para = join_paras(t_paras[1:])
    #set up sequences of tokens
    (i_para, l_para, r_para) = [X[1:] for X in (i_para, l_para, r_para)]
    mid = len(i_para) * len(l_para)/(len(l_para) + len(r_para))
    i_para_seq = i_para[mid - 10:mid + 10]
    filters.linebreak_to_space(i_para_seq)
    i_para_seq = [tuple(X) for X in i_para_seq]
    t_para_seq = l_para[-10:] + r_para[:10]
    filters.linebreak_to_space(t_para_seq)
    t_para_seq = [tuple(X) for X in t_para_seq]
    #match sequence blocks
    sm = difflib.SequenceMatcher(None, tuple(i_para_seq), tuple(t_para_seq))
    mb = sm.get_matching_blocks()
    #determine breakpoint
    l = len(l_para[-10:]); c = 0;
    while mb[c][1] < l: c += 1
    breakpoint = mid
    if c: breakpoint = mid - 10 + mb[c - 1][0] + l
    retval = i_para[:breakpoint]
    while retval and retval[-1][1] in (tokenise.TYPE_SPACE, tokenise.TYPE_LINEBREAK): del retval[-1]
    retval.append(["\n", tokenise.TYPE_LINEBREAK])
    retval.insert(0, sig(retval))
    rem = i_para[breakpoint:]
    rem.insert(0, sig(rem))
    return [retval] + break_para(t_paras[1:], rem) #recursive call


def process_matches(matches, t_para_list, i_para_list):
    #modify i_para_list and matches for joins
    for c, m in enumerate(matches):
        if len(m[1]) > 1:
            joined_para = []
            for ci in m[1]:
                joined_para += i_para_list[ci][1:]
            joined_para.insert(0, sig(joined_para))
            i_para_list.append(joined_para)
            matches[c][1] = [len(i_para_list) - 1]
    #modify i_para_list and matches for splits
    new_matches = []
    for c, m in enumerate(matches):
        if len(m[0]) > 1:
            t_paras = []
            for i in m[0]:
                t_paras.append(t_para_list[i])
            split_paras = break_para(t_paras, i_para_list[m[1][0]])
            for d, i in enumerate(m[0]):
                i_para_list.append(split_paras[d])
                new_matches.append([[i], [len(i_para_list) - 1]])
            matches[c] = None
    matches += new_matches
    matches = [X for X in matches if X]
    matches.sort()
    return matches


def main():
    #process input file into para list
    i_tokens = tokenise.tokenise(file(sys.argv[1]).read())
    i_para_list = split_paras(i_tokens)
    #process token file into para list
    t_tokens = tokenise.tokenise(file(sys.argv[2]).read())
    t_para_list = split_paras(t_tokens)
    #find exact matches
    exact_matches = match_paras(t_para_list, i_para_list)
    matches = []
    for start, end in zip([[-1, -1]] + exact_matches,
                          exact_matches + [[len(t_para_list), len(i_para_list)]]):
        matches.append([[X] for  X in start])
        start = [X + 1 for X in start]
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
    for m in matches: print m
    matches = process_matches(matches, t_para_list, i_para_list)
    print "-----"
    for m in matches: print m
    outdict = dict([(X[0][0], X[1][0]) for X in matches])
    outstrings = []
    for c in range(0, len(t_para_list)):
        if outdict.has_key(c):
            outstrings.append(common.dump_tokens(i_para_list[outdict[c]][1:], True))
        else:
            outstrings.append(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n" +
                              common.dump_tokens(t_para_list[c][1:], True)
                              + ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    file(sys.argv[3], "w").write("\n".join(outstrings).encode("utf-8"))


main()
