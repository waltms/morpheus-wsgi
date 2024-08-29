from urllib.parse import parse_qs
from html import escape
import sys, os, re
import subprocess
import beta_code

morpheus_bin = "bin/cruncher"
morpheus_path = "/var/www/wsgi/morpheus/"
acceptable_referers = ['your.own.referer.com'] # Your approved list of referers. Only used if need_referer = True
logeion_url = "https://logeion.uchicago.edu/"
need_referer = False

# You likely won't need to make changes here

exclude_endings = ['perf', 'perf2', 'conj', 'perf_act', 'fut', 'adj', 'aor', 'comp', 'tr', 'primary', 'secondary', 'irreg', 'decl3', 'act', 'reg', 'aor1', 'aor2', 'short', 'pass', 'vow', 'stem', 'contr', 'denom', 'ath', 'g', 'gx', 'gg', 'mp', 'pr'] # pos info that is English-ish

### Do not modify below this unless you know what you're doing

def referer_check(env):
    if 'HTTP_REFERER' in env and need_referer:
        referer = env['HTTP_REFERER']
        for host in acceptable_referers:
            if host in referer: return True
        return False
    return not need_referer

def word_check(env):
    params = parse_qs(env['QUERY_STRING'])
    word = params.get('word')

    if word:
        word = beta_code.greek_to_beta_code(word[0])
        #word = escape(word)
        return word
    return False

def input_check(env):
    params = parse_qs(env['QUERY_STRING'])
    input_box = params.get('input')

    if input_box:
        return True
    else:
        return False

def word_sanitize(word):
    word = str(word).replace(r'—', '\u0304')
    #word = str(word).replace(r'\u00b7', ':')
    return word

def to_greek_endings(grams):
    new_grams = []
    for gram in grams.split(' '):
        new_gram = []
        excluded_found = False
        for endings in gram.split(','):
            new_endings = []
            for ending in endings.split('_'):
                ending = ending.strip()
                if ending not in exclude_endings:
                    new_endings.append("-%s" % beta_code.beta_code_to_greek(ending))
                else:
                    excluded_found = True
                    new_endings.append(ending)
            if not excluded_found:
                new_gram.append('/'.join(new_endings))
            else:
                new_gram.append('_'.join(new_endings))
        new_grams.append(', '.join(new_gram))
    return ' '.join(new_grams)

def parse_word(word, flags="S"):
    cruncher = os.path.join(morpheus_path, morpheus_bin)
    flags = ' '.join(['-' + f for f in flags])
    command = ' '.join(['echo', '"' + word + '"', '| MORPHLIB=stemlib', cruncher, flags])
    morpheus = subprocess.run([command], capture_output=True, shell=True, cwd=morpheus_path, encoding='utf8')
    if morpheus.stdout:
        return str(morpheus.stdout)
    return None

def morpheus_to_html(morpheus_result, input_box):

    path = os.path.join(morpheus_path, "morpheus.html")
    file = open(path, "r")
    html = file.read()

    # split on <NL>
    result = morpheus_result.replace('</NL>', '')
    result = result.split('<NL>')
    for lemmaline in result:

#        # fix spacing and punctuation
        idx = result.index(lemmaline)
        sections = lemmaline.split(' ')
        if len(sections) > 1:
            words = []
            for word in sections[1].split(','):
                word = beta_code.beta_code_to_greek(word)
                word = word_sanitize(word)
                words.append('<a href='+ logeion_url + re.sub(r'[0-9]*', '', str(word)) + '>' + word + '</a>')
            sections[1] = "%s: " % ', '.join(words)
            result[idx] = ' '.join(sections[1:])
        else:
            result[idx] = "Search token: %s" % beta_code.beta_code_to_greek(sections[0])

        tab_sections = result[idx].split('\t')
        if len(tab_sections) > 1:
            if tab_sections[1]: tab_sections[1] = "(%s)" % tab_sections[1]
            if "_" in tab_sections[-1]: tab_sections[-1] = to_greek_endings(tab_sections[-1])
            result[idx] = ' '.join(tab_sections)

    # join with <br>
    out_html = '<div style="position:relative; margin: 0 auto; display: inline-block; border-radius: 10px; border: 2px solid #800000; padding: 20px;">%s</div>' % '<br>'.join(result)
    html = html.replace("%WORDS%", out_html)
    if input_box:
        html = html.replace("%DISPLAY%", "")
    else:
        html = html.replace("%DISPLAY%", "display: none;")

    return html

def application(env, start_response):

    start_response('200 OK', [('Content-Type','text/html')])

    if referer_check(env):
        word = word_check(env)
        if word:
            morpheus_result = parse_word(word)
            if morpheus_result:
                input_box = input_check(env)
                result = morpheus_to_html(morpheus_result, input_box)
                return[bytes(result, 'utf8')]
            else:
                return[b'Unknown word.']
        else:
            return[b'No word supplied.']
    else:
        return[b'Please search Logeion first.']
