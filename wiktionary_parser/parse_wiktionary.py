''' Utility that takes an XML dump of wiktionary and outputs a json file of words that we can call our bros. '''

import re
from hyphenate import hyphenate_word
from pprint import pprint
import json

class WordUsed(Exception): pass

title = ''
title_re = re.compile('<title>([^<]+)</title>')

# Regexes that match phonemes. 
# Most wiktionary words don't provide an X-SAMPA pronunciation, so our search could probably be improved by using a pronunciation style that uses unicode.
sampa_re_uh = re.compile('{{X-SAMPA\|/(\S*@\S*/)}}')
sampa_re_oh = re.compile('{{X-SAMPA\|/(\S*oU\S*/)}}')
words = set()
type = 'Unknown'
with open('enwiktionary-latest-pages-meta-current.xml') as f:
    for i, line in enumerate(f):
        m = title_re.search(line)
        if m:
            # The title of a wiktionary article is the word itself
            title = m.group(1)

        ## Only output lines that are a certain type of speech.
        ## This ends up limiting the results much more than intended, since many words aren't listed in all forms, if a form is listed at all.
        #for t in 'Noun', 'Verb', 'Proper noun', 'Adverb', 'Adjective':
        #    if t in line:
        #        type = t
        #        break
        m = sampa_re_oh.search(line)
        if m:
            #print i, title, m.group().replace('&quot;', '"')
            #if type in ('Noun', 'Proper noun'):
            words.add(title)
            #if type == 'Verb':
            #    print i, title
            #type = 'Unknown'
            # uncomment this block when trying new heuristics so that we don't have to scan the whole wiktionary
            # if i > 10000000:
            #     break

print len(words)
output = []
for w in words:
    parts = hyphenate_word(w)
    if len(parts) > 1:
        try:
            # Try a bunch of heuristics to turn the word into something coherant after we've crammed a bro in there
            for i, p in enumerate(parts):
                if i == 0 and p[1] == 'o':
                    parts[i] = 'BRO' + p[2:]
                    raise WordUsed()
                if len(p) == 2 and p[1] == 'o':
                    if i > 0 and p[0] in 'tgvdnl':
                        parts[i] = p[0] + 'BRO'
                    else:
                        parts[i] = 'BRO'
                    raise WordUsed()
                elif p.startswith('o'):
                    parts[i] = 'BR' + p
                    raise WordUsed()
                elif p.startswith('ro'):
                    parts[i] = p.replace('ro', 'BRO')
                    raise WordUsed()
                elif 'ro' in p:
                    parts[i] = 'BRO'
                    raise WordUsed()
        # Sure, this could be a function. OR we could abuse exceptions and use them as a goto, which is way more fun.
        except WordUsed:
            output.append(''.join(parts))
        else:
            #Print the word so we can see why it wasn't matched
            print '-'.join(parts)
        #print w, '-'.join(parts)
       
with open('broutput.json', 'w') as out:
   json.dump(output, out)
print 'Done'