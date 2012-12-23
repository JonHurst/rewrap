#!/usr/bin/python

import re

(TYPE_UNKNOWN, TYPE_WORD, TYPE_DIGIT,
 TYPE_SPACE, TYPE_PUNC, TYPE_NOTE,
  TYPE_LINEBREAK, TYPE_PARABREAK, TYPE_PAGEBREAK) = (
    0x00, 0x01, 0x02,
    0x04, 0x08, 0x10,
    0x20, 0x40, 0x80)

token_description = dict(zip(
    [0x00, 0x01, 0x02,
    0x04, 0x08, 0x10,
    0x20, 0x40, 0x80],
    ["Unknown", "Word", "Digit",
     "Space", "Punctuation", "Note",
     "Linebreak", "Parabreak", "Pagebreak" ]))

pending_pagebreak = None

def tokenise(text):
    tokens = []
    regexp_notes = re.compile(r"(\[\*\*[^\]]*\])", re.UNICODE)
    regexp_words = re.compile(r"([^\W_]+)", re.UNICODE)
    regexp_digits = re.compile(r"([\d]+)", re.UNICODE)
    regexp_breaks = re.compile(r"(\n+)", re.UNICODE)
    regexp_whitespace = re.compile(r"([\s]+)", re.UNICODE)
    regexp_pagebreaks = re.compile(r"\n=====#([\d]+)#=====", re.UNICODE)

    def process_digits(text):
        text_sections = regexp_digits.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                tokens.append([s, TYPE_DIGIT])
            else:
                tokens.append([s, TYPE_WORD])

    def process_words(text):
        text_sections = regexp_words.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                process_digits(s)
            else:
                process_whitespace(s)

    def process_whitespace(text):
        text_sections = regexp_whitespace.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                process_breaks(s)
            else:
                tokens.append([s, TYPE_PUNC])

    def process_breaks(text):
        global pending_pagebreak
        text_sections = regexp_breaks.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                if pending_pagebreak:
                    tokens.append([s[:1], TYPE_LINEBREAK|TYPE_PAGEBREAK, pending_pagebreak])
                    pending_pagebreak = None
                else:
                    tokens.append([s[:1], TYPE_LINEBREAK])
                if len(s) > 1:
                    tokens[-1][1] |= TYPE_PARABREAK
            else:
                tokens.append([s, TYPE_SPACE])

    def process_notes(text):
        text_sections = regexp_notes.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                tokens.append([s, TYPE_NOTE])
            else:
                process_words(s)

    def process_pagebreaks(text):
        global pending_pagebreak
        text_sections = regexp_pagebreaks.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                pending_pagebreak = s
            else:
                process_notes(s)

    process_pagebreaks(text.rstrip())
    if pending_pagebreak:
        final_break = ["\n", TYPE_LINEBREAK|TYPE_PAGEBREAK, pending_pagebreak]
    else:
        final_break = ["\n", TYPE_LINEBREAK]
    return [X for X in tokens if len(X[0])] + [final_break]
