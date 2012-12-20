#!/usr/bin/python
# -*- coding: utf-8 -*-

import tokenise
import sys
import difflib
import math
import glob
import os.path
from common import split_paras, sig, dump_tokens, linebreak_to_space

match_criteria = 0.85


def make_para_dict(para_list):
    """Take a para_list (as output by common.split_paras) and create a dictionary with the para's sig as
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
    intersection = t_sig & i_sig
    max_intersection_len = min(len(t_sig), len(i_sig))
    #match criteria is global set at the top of this file
    if float(len(intersection))/max_intersection_len < match_criteria : return False
    t_match = float(len(intersection)) / len(t_sig)
    i_match = float(len(intersection)) / len(i_sig)
    return (t_match, i_match)


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


def break_para(t_paras, i_para):
    """Breaks i_para into a list of paras that approximately match those in the t_paras list"""
    if len(t_paras) == 1: return [i_para] #recursive terminator
    l_para = t_paras[0]
    r_para = join_paras(t_paras[1:])
    (i_para, l_para, r_para) = [X[1:] for X in (i_para, l_para, r_para)]
    #calculate window size
    length_dif = len(i_para) - len(l_para) - len(r_para)
    if length_dif > 0:
        window_start = int(0.8 * len(l_para))
        window_end = int(1.2 * len(l_para)) + length_dif
    else:
        window_start = int(0.8 * len(l_para)) + length_dif #nb length_dif negative here
        window_start = max(window_start, 0)
        window_end = int(1.2 * len(l_para))
    #set up sequences of tokens
    i_para_seq = i_para[window_start:window_end]
    linebreak_to_space(i_para_seq)
    i_para_seq = [tuple(X) for X in i_para_seq]
    t_para_seq = (l_para + r_para)[window_start:window_end]
    linebreak_to_space(t_para_seq)
    t_para_seq = [tuple(X) for X in t_para_seq]
    #match sequence blocks
    sm = difflib.SequenceMatcher(None, tuple(i_para_seq), tuple(t_para_seq), False)
    mb = sm.get_matching_blocks()
    #determine breakpoint
    c = 0;
    while mb[c][1] < len(l_para) - window_start: c += 1 #mb[c - 1] is now the last match block inside l_para
    breakpoint = len(l_para) + mb[c - 1][0] - mb[c - 1][1]
    if mb[c - 1][1] + mb[c - 1][2] + 1 < len(l_para) - window_start:
        print "[Warning: Paragraph split occurred outside match block]"
        error_tokens = i_para[max(0, breakpoint - 20):breakpoint]
        print "=============================="
        print dump_tokens(error_tokens, True).encode("utf-8")
        print "------------------------------"
        error_tokens = l_para[-20:]
        print dump_tokens(error_tokens, True).encode("utf-8")
        print "==============================\n"
    retval = i_para[:breakpoint]
    while retval and (retval[-1][1] & (tokenise.TYPE_SPACE | tokenise.TYPE_LINEBREAK)): del retval[-1]
    retval.append(["\n", tokenise.TYPE_LINEBREAK | tokenise.TYPE_PARABREAK])
    retval.insert(0, sig(retval))
    rem = i_para[breakpoint:]
    rem.insert(0, sig(rem))
    return [retval] + break_para(t_paras[1:], rem) #recursive call


def process_matches(matches, t_para_list, i_para_list):
    #modify i_para_list and matches for joins
    for c, m in enumerate(matches):
        if len(m[1]) > 1:
            joined_para = []
            print "[Info: Joining input paragraphs %s]" % ", ".join([str(X) for X in m[1]])
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
            print "[Info: Splitting input paragraph %04d based on template paragraphs %s]" % (
                m[1][0], ", ".join([str(X) for X in m[0]]))
            for i in m[0]:
                t_paras.append(t_para_list[i])
            split_paras = break_para(t_paras, i_para_list[m[1][0]])
            for d, i in enumerate(m[0]):
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


def build_output(t_para_list, i_para_list, matches):
    outdict = {}
    for m in matches:
        if not outdict.has_key(m[0][0]):#chooses first match if multiples
            outdict[m[0][0]] = m[1][0]
    outstrings = []
    t_count, i_count = 0, 0
    for c in range(0, len(t_para_list)):
        desc = str(c)
        if outdict.has_key(c):
            outstrings.append(dump_tokens(i_para_list[outdict[c]][1:], True))
            i_count += len(i_para_list[outdict[c]][1:])
        else:
            print "[Warning: Retaining template paragraph %04d]" % c
            outstrings.append(dump_tokens(t_para_list[c][1:], True))
            t_count += len(t_para_list[c][1:])
    print "t_count:", t_count, "i_count:", i_count, "rep_rate:", str(i_count * 100 / (t_count + i_count)) + "%"
    return "\n".join(outstrings)


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
    #process token lists
    matches = build_match_list(t_para_list, i_para_list)
    matches = process_matches(matches, t_para_list, i_para_list)
    for m in matches:
        print "%04d = %04d : %3d%%" % (m[0][0], m[1][0], int(math.ceil(min(*m[2]) * 100)))
    output = build_output(t_para_list, i_para_list, matches)
    file(sys.argv[2] + ".paramatch", "w").write(output.encode("utf-8"))


if __name__ == "__main__":
    main()
