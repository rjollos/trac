#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os.path
import re
import sys

from pkg_resources import resource_listdir, resource_string

from trac.loader import load_components
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.util.text import printerr, printout
from trac.web.chrome import web_context
from trac.web.href import Href
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage

try:
    import pypandoc
except ImportError:
    printerr("The pypandoc package must be installed.")
    sys.exit(1)


def wiki2rest(env, context, wiki):
    text = re.sub('\r?\n', '\n', wiki.text)
    text = re.sub(r'\[\[TracGuideToc\]\]\r?\n?', '', text)
    text = re.sub(r'\[\[PageOutline\([^\)]*\)\]\]\r?\n?', '', text)
    html = str(format_to_html(env, context, text))
    html = html.replace('<span class="icon">\u200b</span>', '')
    html = re.sub(r'<em>\s*([^<]*?)\s*</em>', r'<em>\1</em>', html)
    html = '<html><body>%s</body></html>' % html
    rst = pypandoc.convert_text(html, 'rst', 'html')
    rst = re.sub('\n{4,}', '\n\n\n', rst)
    # sort links
    rst = re.sub(r'(?:\n\.\. _[^\n]*)+\Z',
                 lambda m: '\n'.join(sorted(m.group(0).split('\n'),
                                            key=lambda v: v.lower())),
                 rst)
    if any(ord(c) > 0x7f for c in rst):
        # Trac detects utf-8 using BOM
        rst = '%s.. charset=utf-8\n\n%s' % (codecs.BOM_UTF8, rst)
    return rst + '\n'


def main():
    names = sorted(name for name in resource_listdir('trac.wiki',
                                                     'default-pages')
                        if not name.startswith('.'))

    env = EnvironmentStub()
    load_components(env)
    with env.db_transaction:
        for name in names:
            wiki = WikiPage(env, name)
            wiki.text = resource_string('trac.wiki', 'default-pages/' +
                                        name).decode('utf-8')
            if wiki.text:
                wiki.save('trac', '')
            else:
                printout('%s: Skipped empty page' % name)

    req = Mock(href=Href('/'), abs_href=Href('https://trac.edgewall.org/'),
               perm=MockPerm(), chrome={})
    for name in sys.argv[1:]:
        name = os.path.basename(name)
        wiki = WikiPage(env, name)
        if not wiki.exists:
            continue
        context = web_context(req, wiki.resource, absurls=True)
        rst = wiki2rest(env, context, wiki)
        sys.stdout.write(rst)


if __name__ == '__main__':
    main()
