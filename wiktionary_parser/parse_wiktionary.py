#/usr/bin/env python
# coding: utf-8
"""Parse an XML dump of all US-english wiktionary articles."""

# The file mmaped and parsed using a set of regexes. This isn't very elegant,
# but, at the time of this writing, the dump is around 4GiB uncompressed.
# Solutions involving iterating over lines in the file, or using an XML parser
# are all too slow or memory intensive. Even mmaping the file will probably
# fail in 32-bit version of python. If you get a MemoryError when running this
# script, try it with a 64-bit version. This script runs in about a minute on
# a 3.5GHz Core i5.

import csv
import itertools
import mmap
import re
import sys
import json

from hyphenate import hyphenate_word

def broize_syllable(p, i):
    """Given a syllable and its index in an word, return a bro version or None."""
    # Try a bunch of heuristics to turn the word into something coherent after
    # we've crammed a bro in there
    if p == 'bro' or len(p) < 2:
        return None
    if i == 0:
        if p[1] == 'o' and p[2:3] != 'u':
            return 'BRO' + p[2:]
        if p.startswith('chro'):
            return p.replace('chro', 'BRO')
    if len(p) == 2 and p[1] == 'o':
        if i > 0 and p[0] in 'tgvdnl':
            return p[0] + 'BRO'
        else:
            return 'BRO'
    if p[1:3] == 'ro':
        return 'BRO' + p[3:]
    if p[0] == 'o':
        return 'BR' + p
    if 'ro' in p:
        return p.replace('ro', 'BRO')

def make_word(parts, sub, i):
    """Replace a syllable in a list of words, and return the joined word."""
    j = 0
    for part in parts:
        for k in range(len(part)):
            if i == j:
                part[k] = sub
                return ' '.join(''.join(p for p in part) for part in parts)
            j += 1

def broize(word, ipa):
    """Given a word and its IPA pronunciation, return a bro version of the word, or None."""
    parts = [hyphenate_word(w) for w in word.split()]
    flat_parts = list(itertools.chain.from_iterable(parts))
    if len(flat_parts) < 2:
        return None

    # Find the syllable that contains the phoneme we're going to replace. IPA
    # uses periods to represent syllable breaks. Not all pronunciations have
    # them, unfortunately.
    if '.' in ipa:
        i = ipa.count('.', 0, ipa.find('oʊ'))
        try:
            broized = broize_syllable(flat_parts[i], i)
        except IndexError:
            # Sometimes hyphenate returns a result that's shorter than the IPA
            # suggests.
            pass
        else:
            if broized is None:
                return None
            return make_word(parts, broized, i)

    # Try all the syllables as a last resort
    for i, p in enumerate(flat_parts):
        broized = broize_syllable(p, i)
        if broized is not None:
            return make_word(parts, broized, i)
    return None

class JsonWriter(object):
    """Write lists to a json file with the same interface as csv.Writer."""
    def __init__(self, out):
        self.out = out

    def writerow(self, row):
        # Don't write the original word in json format
        json.dump(row[1:], self.out)
        self.out.write(',\n')

# The following regexes are used to parse the mmaped xml file. 
pronunciation_re = re.compile(r'a\|US.+/([^/]*oʊ[^/ɹɾ]*)/')
title_re = re.compile(r'<title>([^<]+)</title>')
english_re = re.compile(r'==English==\n.+?(?:\n==\w|\Z)', flags=re.S)
speech_part_re = re.compile(r'==(Verb|Noun|Proper noun|Adjective|Adverb)==')
page_re = re.compile(rb'<page>.+?</page>', flags=re.S)

def main(limit=sys.maxsize, format='json'):
    i = 0

    with open('output.' + format, 'w', encoding='utf-8', newline='') as fout:
        if format == 'csv':
            writer = csv.writer(fout)
            writer.writerow(('word', 'broized', 'part of speech'))
        else:
            fout.write('[\n')
            writer = JsonWriter(fout)
        try:
            with open('enwiktionary.xml', encoding='utf-8') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    for match in page_re.finditer(mm):
                        page = match.group().decode('utf-8')
                        try:
                            pronunciation = pronunciation_re.search(page).group(1)
                            title = title_re.search(page).group(1)
                            if ':' in title: 
                                continue

                            english_section = english_re.search(page).group()
                            speech_part = speech_part_re.search(english_section).group(1)
                        except AttributeError:
                            # If any of the regexes fail to match, an
                            # AttributeError is raised
                            continue
                        broized = broize(title, pronunciation)
                        if broized is not None:
                            i += 1
                            writer.writerow((title, broized, speech_part))
                        if i > limit:
                            return
        finally:
            if format == 'json':
                fout.write(']\n')

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('limit', type=int, nargs='?', default=sys.maxsize)
    parser.add_argument('--format', choices=['json', 'csv'], default='json')
    args = parser.parse_args()
    main(args.limit)