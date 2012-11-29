#!/usr/bin/python
# -*- coding: utf-8 -*-

import tokenise
import filters
import glob
import difflib
import hashlib
import sys

final_directory = "/home/jon/proj/frankenstein/final/"
final_directory = "/home/jon/proj/frankenstein/extant/"
#final_text = final_directory + "test.txt"
final_text = final_directory + "pg41445.txt"
final_text = final_directory + "pg84.txt"

p3_directory = "/home/jon/proj/frankenstein/p3/"
#p3_text = p3_directory + "00*"
p3_text = p3_directory + "???"

def build_token_list(files):
    files = glob.glob(files)
    files.sort()
    tokens = []
    for f in files:
        tokens.append(["-----" + f + "-----\n", tokenise.TYPE_PAGEBREAK])
        file_tokens = tokenise.tokenise(file(f).read())
        if file_tokens[0][1] == tokenise.TYPE_LINEBREAK:
            file_tokens[0][1] = tokenise.TYPE_PARABREAK
        tokens += file_tokens
    return tokens


def dump_tokens(token_list, astext=False):
    if astext:
        outstr = ""
        for t in token_list:
            outstr += t[0]
        print outstr
    else:
        for t in token_list:
            print "{", tokenise.token_description[t[1]], "}:", t[0]


def sig(tokens):
    word_set = set()
    repeat_set = set()
    for t in tokens:
        if t[1] == tokenise.TYPE_WORD:
            s = t[0].lower()
            if s in word_set:
                repeat_set.add(s)
            else:
                word_set.add(s)
    return (frozenset(word_set), frozenset(repeat_set))



def split_paras(token_list):
    para_list = []
    para = []
    name = ""
    for t in token_list:
        if t[1] == tokenise.TYPE_PARABREAK:
            s = sig(para)
            para_list.append((para, s[0], s[1]))
            para = []
        else:
            para.append(t)
    return para_list


def intersect_dicts(dict1, dict2):
    intersection = set(dict1.keys()) & set(dict2.keys())
    for k in dict1.keys():
        if k not in intersection: del dict1[k]
    for k in dict2.keys():
        if k not in intersection: del dict2[k]


def make_para_dict(para_list):
    para_dict = {}
    for c, para_desc in enumerate(para_list):
        key = para_desc[1]
        if para_dict.has_key(key):
            para_dict[key] = -1
        else:
            para_dict[key] = c
    for k in para_dict.keys():
        if para_dict[k] == -1:
            del para_dict[k]
    return para_dict



def match_paras(para_list_1, para_list_2):
    para_dict_1 = make_para_dict(para_list_1)
    para_dict_2 = make_para_dict(para_list_2)
    intersect_dicts(para_dict_1, para_dict_2)
    para_match_list = [[0, 0]]
    for k in para_dict_1.keys():
        para_match_list.append([para_dict_1[k], para_dict_2[k]])
    para_match_list.append([len(para_list_1), len(para_list_2)])
    para_match_list.sort()
    return para_match_list


def dump_dict(d):
    items = d.items()
    items = [(X[1], X[0]) for X in items]
    items.sort()
    for i in items:
        print i


def dump_mismatches(matches, para_list_1, para_list_2):
    count = 0
    for p in zip(matches[:-1], matches[1:]):
        length_diff = (p[1][0] - p[0][0]) - (p[1][1] - p[0][1])
        if length_diff:
            print length_diff, p
            if count > 2: continue
            c1, c2 = p[0][0], p[0][1]
            print "=============================="
            while c1 <= p[1][0] or c2 <= p[1][1]:
                if c1 <= p[1][0]:
                    outstr = "{{"
                    for t in para_list_1[c1]:
                        outstr += t[0]
                    outstr += "}}"
                    outstr = outstr.replace("\n", " ")
                    if len(outstr) < 60:
                        print outstr
                    else:
                        print outstr[:30] + "..." + outstr[-30:]
                if c2 <= p[1][1]:
                    outstr = "[["
                    for t in para_list_2[c2]:
                        outstr += t[0]
                    outstr += "]]"
                    outstr = outstr.replace("\n", " ")
                    if len(outstr) < 60:
                        print outstr
                    else:
                        print outstr[:30] + "..." + outstr[-30:]
                c1 += 1; c2 += 1;
            count += 1
            print "=============================="


def make_word_dict(tokens):
    word_dict = {}
    for c, t in enumerate(tokens):
        if t[1] == tokenise.TYPE_WORD:
            if word_dict.has_key(t[0]):
                word_dict[t[0]] = -1
            else:
                word_dict[t[0]] = c
    for key in word_dict.keys():
        if word_dict[key] == -1:
            del word_dict[key]
    return word_dict


def rewrap_para(source, target):
    word_dict_source = make_word_dict(source)
    word_dict_target = make_word_dict(target)
    intersect_dicts(word_dict_source, word_dict_target)
    matches = [[0, 0, None]]
    for k in word_dict_source.keys():
        matches.append([word_dict_source[k], word_dict_target[k], k])
    matches.append([len(source), len(target), None])
    matches.sort()
    retval = []
    for m in zip(matches[:-1], matches[1:]):
        source_shard = source[m[0][0]:m[1][0]]
        target_shard = target[m[0][1]:m[1][1]]
        merge_breaks(source_shard, target_shard)
        retval += source_shard
    return retval


def process_same_length_shards(source, target):
    for c, t in enumerate(target):
        if t[1] == tokenise.TYPE_LINEBREAK:
            if source[c][1] == tokenise.TYPE_SPACE:
                source[c] = t
            else:
                insert_into_next_space(source, c + 1, ["¶" + t[0], t[1]])
        elif t[1] == tokenise.TYPE_PAGEBREAK:
            source.insert(c, t)
    return source


def insert_into_next_space(source, c, token):
    while (c < len(source)
           and source[c][1] !=tokenise.TYPE_SPACE):
        c += 1
    if c >= len(source):
        source.append(token)
    else:
        source[c] = token


def process_diff_length_shards(source, target):
    clean_target = target[:]
    for c, t in enumerate(clean_target):
        if t[1] == tokenise.TYPE_LINEBREAK:
            clean_target[c] = [" ", tokenise.TYPE_SPACE]
    #break the shard into three parts
    from_start = 0
    while from_start < len(source) and from_start <len(clean_target):
        if source[from_start] != clean_target[from_start]: break
        from_start += 1
    #from_start is the index of the first token that does not match
    from_end = -1
    while (len(source) + from_end >= from_start and
           len(clean_target) + from_end >= from_start):
        if source[from_end] != clean_target[from_end]: break
        from_end -= 1
    #from_end is the index of the last token that does not match
    debug_msg("%s, %s" % (from_start,from_end))
    if from_start > 0:
        debug_msg("subshard-startb: " + str(source[:from_start]))
        source[:from_start] = process_same_length_shards(source[:from_start], target[:from_start])
        debug_msg("subshard-starta: " + str(source[:from_start]))
    if from_end < -1:
        debug_msg( "subshard-endb: " + str(source[from_end + 1:]))
        source[from_end + 1:] = process_same_length_shards(source[from_end + 1:], target[from_end + 1:])
        debug_msg("subshard-enda: " + str(source[from_end + 1:]))
    debug_msg("subshard-mid-source: " + str(source[from_start:len(source) + from_end + 1]))
    debug_msg("subshard-mid-target: " + str(target[from_start:len(target) + from_end + 1]))
    mid_shard = source[from_start:len(source) + from_end + 1]
    for c, t in enumerate(target[from_start:len(target) + from_end + 1]):
        debug_msg( "processing mid shard: " + str(c))
        if t[1] == tokenise.TYPE_LINEBREAK:
            insert_into_next_space(mid_shard, c, ["¶" + t[0], t[1]])
        elif t[1] == tokenise.TYPE_PAGEBREAK:
            mid_shard.insert(c, t)
    source[from_start:len(source) + from_end + 1] = mid_shard


def debug_msg(str):
#    print str
    pass

def merge_breaks(source, target):
    # for c, t in enumerate(target):
    #     if t[1] == tokenise.TYPE_PAGEBREAK:
    #         source.insert(c, t)
    debug_msg("sb: " + str(source))
    debug_msg("t: " + str(target))
    if len(source) == len(target):
        process_same_length_shards(source, target)
    else:
        process_diff_length_shards(source, target)
    debug_msg("sa: " + str(source) + "\n")


def fuzzy_match_paras(pair1, pair2, list_1, list_2):
    match_list = []
    para_list_1 = list_1[pair1[0] + 1:pair2[0]]
    para_list_2 = list_2[pair1[1] + 1:pair2[1]]
    match_list.append([[pair1[0]], [pair1[1]], 100, 100])
    for c1, p1 in enumerate(para_list_1):
        if not p1[1]: continue
        for c2, p2 in enumerate(para_list_2):
            if not p2 or not p2[1] or not para_list_2[c2]: continue
            intersection = p1[1] & p2[1]
            match_perc_1 = len(intersection) * 100 / len(p1[1])
            match_perc_2 = len(intersection) * 100 / len(p2[1])
            min_match_perc = min(match_perc_1, match_perc_2)
            max_match_perc = max(match_perc_1, match_perc_2)
            if min_match_perc < 30 or max_match_perc < 90: #somewhat certain no match
                continue
            match_list.append([[pair1[0] + c1 + 1], [pair1[1] + c2 + 1],
                               match_perc_1, match_perc_2])
    return match_list


def create_para_match_version(i, template):
    i_tokens = build_token_list(i)
    i_tokens = filters.run_filters(i_tokens, (
            filters.linebreak_to_space,
            filters.remove_formatting
            ))
    i_para_list = split_paras(i_tokens)
    template_tokens = build_token_list(template)
    template_tokens = filters.run_filters(template_tokens, (
            filters.remove_formatting,
            filters.remove_notes,
            filters.recombine_words_split_by_pagebreak
            ))
    template_para_list = split_paras(template_tokens)
    matches = match_paras(template_para_list, i_para_list)
    match_list = []
    for pair1, pair2 in zip(matches[:-1], matches[1:]):
        match_list += fuzzy_match_paras(pair1, pair2, template_para_list, i_para_list)
    para_set = set(range(1, len(template_para_list)))
    match_para_set = set([X[0][0] for X in match_list])
    para_set -= match_para_set
    print_list = list(para_set)
    print_list.sort()
    for p in print_list:
        print p


def main():
    create_para_match_version(final_text, p3_text)
    sys.exit(0)


    final_tokens = build_token_list(final_text)
    final_tokens = filters.run_filters(final_tokens, (
            filters.linebreak_to_space,
#            filters.remove_formatting
            ))
    final_para_list = split_paras(final_tokens)
    p3_tokens = build_token_list(p3_text)
    p3_tokens = filters.run_filters(p3_tokens, (
            filters.remove_formatting,
            filters.remove_notes,
            filters.recombine_words_split_by_pagebreak
            ))
#    dump_tokens(p3_tokens)
    p3_para_list = split_paras(p3_tokens)
    matches = match_paras(p3_para_list, final_para_list)
    # for m in matches[1:-1]:
    #     print m
    #     print "------------------------------"
    #     dump_tokens(final_para_list[m[0]][0], True)
    #     print "=============================="
    #     dump_tokens(p3_para_list[m[1]][0], True)
    #     print "------------------------------"
    for pair1, pair2 in zip(matches[:-1], matches[1:]):
        print "++", pair1
        fuzzy_match_paras(pair1, pair2, p3_para_list, final_para_list)
#    dump_mismatches(matches, final_para_list, p3_para_list)
#    sys.exit(0)
#     outstr = ""
#     for (source, target) in zip(final_para_list, p3_para_list):
#         para = rewrap_para(source, target)
# #        dump_tokens(para)
#         for t in para:
#             outstr += t[0]
#         outstr += "\n"
#     print outstr

main()

