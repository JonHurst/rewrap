#!/usr/bin/python

import tokenise


def run_filters(tokens, filter_list):
    for f in filter_list:
        f(tokens)
    return [X for X in tokens if X[1] != tokenise.TYPE_UNKNOWN]


def linebreak_to_space(tokens):
    for c, t in enumerate(tokens):
        if t[1] == tokenise.TYPE_LINEBREAK:
            tokens[c] = [" ", tokenise.TYPE_SPACE]


def remove_formatting(tokens):
    for c, t in enumerate(tokens):
        if t[1] == tokenise.TYPE_PUNC:
            newstring = t[0].replace("_", "")
            if newstring:
                tokens[c][0] = newstring
            else:
                tokens[c][1] = tokenise.TYPE_UNKNOWN


def remove_notes(tokens):
    for c, t in enumerate(tokens):
        if t[1] == tokenise.TYPE_NOTE:
            tokens[c] = ["", tokenise.TYPE_UNKNOWN]
            #deal with note with space on both sides
            if (c > 0 and c < len(tokens) - 1
                and tokens[c - 1][1] == tokenise.TYPE_SPACE
                and tokens[c + 1][1] == tokenise.TYPE_SPACE):
                tokens[c + 1][1] = tokenise.TYPE_UNKNOWN


def recombine_words_split_by_pagebreak(tokens):
    for c, t in enumerate(tokens):
        if (t[1] == tokenise.TYPE_PAGEBREAK
            and c - 4 >= 0  and c + 1 < len(tokens)
            and tokens[c - 2][0] == "-*"
            and tokens[c - 3][1] == tokenise.TYPE_WORD):
            if tokens[c + 1][0] == "*":
                tokens[c + 1][1] = tokenise.TYPE_UNKNOWN
            if tokens[c - 4][1] == tokenise.TYPE_SPACE:
                tokens[c - 4][1] = tokenise.TYPE_UNKNOWN
            tokens[c - 3][1] = tokens[c - 2][1] = tokenise.TYPE_UNKNOWN


