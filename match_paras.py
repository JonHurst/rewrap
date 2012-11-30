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


def intersect_percentages(t_sig, i_sig):
    intersection = t_sig & i_sig
    t_match_perc = len(intersection) * 100 / len(t_sig)
    i_match_perc = len(intersection) * 100 / len(i_sig)
    return (t_match_perc, i_match_perc)


def intersect_candidates(t_candidate, t_paras, i_candidate, i_paras):
    t_candidate_sig = set()
    for i in t_candidate:
        t_candidate_sig |= t_paras[i][0]
    i_candidate_sig = set()
    for i in i_candidate:
        i_candidate_sig |= i_paras[i][0]
    return intersect_percentages(t_candidate_sig, i_candidate_sig)


def fuzzy_match_paras(t_paras, i_paras):
    """Find matches in the t_paras list and i_paras list. The sigs in these lists may be None if an
    exact matches have already been made."""
    match_list = []
    for ct, pt in enumerate(t_paras):
        if not pt[0]: continue
        for ci, pi in enumerate(i_paras):
            if not pi[0]: continue
            int_percs = intersect_percentages(pt[0], pi[0])
            if min(*int_percs) < 30 or max(*int_percs) < 90: #somewhat certain there is no match
                continue
            match_list.append([[ct], [ci], int_percs])
    #process joins and splits
    c = 0
    while c + 1 < len(match_list):
        #note: need to check these work in more complex cases
        #detect and process join case
        if (match_list[c][0][-1] == match_list[c + 1][0][0] and
            match_list[c][1][-1] + 1 == match_list[c + 1][1][-1]):
            t_candidate = match_list[c][0]
            i_candidate = match_list[c][1] + match_list[c + 1][1]
            int_percs = intersect_candidates(t_candidate, t_paras, i_candidate, i_paras)
            if min(*int_percs) >= 90:
                match_list[c + 1] = [t_candidate, i_candidate, int_percs]
                match_list[c] = None
        #detect and process split case
        elif (match_list[c][0][-1] + 1 == match_list[c + 1][0][0] and
            match_list[c][1][0]  == match_list[c + 1][1][0]):
            t_candidate = match_list[c][0] + match_list[c + 1][0]
            i_candidate = match_list[c][1]
            int_percs = intersect_candidates(t_candidate, t_paras, i_candidate, i_paras)
            if min(*int_percs) >= 90:
                match_list[c + 1] = [t_candidate, i_candidate, int_percs]
                match_list[c] = None
        c += 1
    return match_list



def main():
    #process input file into para list
    i_tokens = tokenise.tokenise(file(input_file).read())
    i_para_list = split_paras(i_tokens)
    #process token file into para list
    t_tokens = tokenise.tokenise(file(template_file).read())
    t_para_list = split_paras(t_tokens)
    #find exact matches
    exact_matches = match_paras(t_para_list, i_para_list)
    matches = [[[X[0]], [X[1]]] for X in exact_matches]
    for start, end in zip([[-1, -1]] + exact_matches,
                          exact_matches + [[len(t_para_list), len(i_para_list)]]):
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
    matches.sort()
    for m in matches:
        print m

main()
