from urllib.parse import parse_qs
from html import escape
import sys, os, re
import subprocess
import beta_code

morpheus_bin = "bin/cruncher"
morpheus_path = "/var/www/wsgi/morpheus/"
acceptable_referers = ['anastrophe2.lib.uchicago.edu', 'anastrophe.lib.uchicago.edu', 'logeion.uchicago.edu', 'logeion.org']
logeion_url = "https://logeion.uchicago.edu/"
need_referer = False

# You likely won't need to make changes here

exclude_endings = ['art', 'irr', 'indecl', 'noun', 'perf', 'verb', 'adj2', 'perf2', 'pron', 'adj1', 'suppl', 'conj', 'perf_act', 'fut', 'adj', 'aor', 'comp', 'tr', 'primary', 'secondary', 'irreg', 'perfp', 'decl3', 'act', 'reg', 'aor1', 'aor2', 'short', 'pass', 'vow', 'stem', 'contr', 'denom', 'ath', 'g', 'gx', 'gg', 'mp', 'pr'] # pos info that is English-ish

exclude_forms = ['indeclform', 'poetic indeclform', 'contr indeclform']

### Do not modify below this unless you know what you're doing

def referer_check(env):
    if 'HTTP_REFERER' in env and need_referer:
        referer = env['HTTP_REFERER']
        for host in acceptable_referers:
            if host in referer: return True
        return False
    return not need_referer

def word_validate(word):
    match = re.search(r'[.: ]', word)
    if match: 
       return False
    match = re.search(r'^\/', word)
    if match: 
       return False
    return True

def word_check(env):
    params = parse_qs(env['QUERY_STRING'])
    word = params.get('word')[0]

    #if word and word_validate(word):
    if word:
        word = beta_code.greek_to_beta_code(word)
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
    #word = re.sub(r'[0-9]*', '', str(word))
    #word = str(word).replace(r'\u00b7', ':')
    return word

def to_greek_endings(grams):
    new_grams = []
    for gram in grams.split(' '):
        print(gram, file=sys.stderr)
        new_gram = []
        excluded_found = False
        for endings in gram.split(','):
            new_endings = []
            for ending in endings.split('_'):
                ending = ending.strip()
                if ending not in exclude_endings:
                    #print("(%s)" % ending, file=sys.stderr)
                    new_endings.append("-%s" % beta_code.beta_code_to_greek(ending))
                else:
                    excluded_found = True
                    new_endings.append(ending)
                #print(new_endings, file=sys.stderr)
            if not excluded_found:
                new_gram.append('/'.join(new_endings))
            else:
                new_gram.append('_'.join(new_endings))
        #print(new_gram, file=sys.stderr)
        new_grams.append(', '.join(new_gram))
    return ' '.join(new_grams)

def parse_word(word, flags="S"):
    if not word_validate(word): return None

    cruncher = os.path.join(morpheus_path, morpheus_bin)
    flags = ' '.join(['-' + f for f in flags])
    #command = ' '.join(['echo', '"' + word + '"', '| MORPHLIB=stemlib', cruncher, flags])
    #command = ['echo', '"' + word + '"', '| MORPHLIB=stemlib', cruncher, flags]
    my_env = os.environ.copy()
    my_env["MORPHLIB"] = "stemlib"
    try:
        #morpheus = subprocess.run([command], capture_output=True, shell=True, cwd=morpheus_path, encoding='utf8')
        morpheus = subprocess.run([cruncher, flags], input=word, capture_output=True, shell=False, env=my_env, cwd=morpheus_path, encoding='utf8')
    except:
        return "The request could not be processed."
    #print(word, file=sys.stderr)
    #print(morpheus.stdout, file=sys.stderr)
    if morpheus.stdout:
        return str(morpheus.stdout)
    return None

def morpheus_to_html(morpheus_result, input_box, msg=""):

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
                # split on potential trailing numbers, separate them and rejoin after betacode conversion
                word_list = re.split(r'(\d+)', word)
                word_list = [c for c in word_list if c]
                word = word_list[0]
                word = beta_code.beta_code_to_greek(word)
                # most words won't have a trailing number, so use try/except
                try:
                    word = word + word_list[1]
                except:
                    pass
                word = word_sanitize(word)
                words.append('<a href='+ logeion_url + re.sub(r'[0-9]*', '', str(word)) + '>' + word + '</a>')
            sections[1] = "%s: " % ', '.join(words)
            result[idx] = ' '.join(sections[1:])
        else:
            if not msg:
                result[idx] = "Search token: %s" % beta_code.beta_code_to_greek(sections[0])

        tab_sections = result[idx].split('\t')
        if len(tab_sections) > 1:
            if tab_sections[1]: tab_sections[1] = "(%s)" % tab_sections[1]
            if "_" in tab_sections[-1]: tab_sections[-1] = to_greek_endings(tab_sections[-1])

            tab_sections = [ts for ts in tab_sections if ts not in exclude_forms]
            result[idx] = ' '.join(tab_sections)

    # join with <br>
    if len(result) > 1:
        out_html = '<div style="position:relative; margin: 0 auto; display: inline-block; border-radius: 10px; border: 2px solid #800000; padding: 20px;">%s</div>' % '<br>'.join(result)
    else:
        out_html = ""
    html = html.replace("%WORDS%", out_html)
    html = html.replace("%MSG%", msg)
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
                #result = morpheus_result
                return[bytes(result, 'utf8')]
            else:
                msg = 'Couldn\'t parse: "%s". Tell us about it?' % word
                input_box = input_check(env)
                result = morpheus_to_html("", input_box, msg)
                return[bytes(result, 'utf8')]
                #return[b'Unknown word.']
        else:
            return[b'No word supplied.']
    else:
        return[b'Please search Logeion first.']
