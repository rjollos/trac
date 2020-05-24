#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2020 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at https://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at https://trac.edgewall.org/log/.

from datetime import datetime
import argparse
import os.path
import sys

from babel.core import negotiate_locale
from babel.messages.pofile import read_po, write_po


class ScriptError(Exception):
    pass


def _is_fuzzy(message):
    return 'fuzzy' in message.flags


def _has_msgstr(message):
    msgstrs = message.string
    if not isinstance(msgstrs, (list, tuple)):
        msgstrs = [msgstrs]
    return any(v for v in msgstrs)


def _open_pofile(filename):
    try:
        with open(filename, 'rb') as f:
            return read_po(f)
    except IOError as e:
        raise ScriptError(e)


def _get_domains():
    return sorted(name[:-4]
                  for name in os.listdir(os.path.join('trac', 'locale'))
                  if name.endswith('.pot'))


def _get_locales(domain):
    def has_pofile(name):
        return os.path.isfile(os.path.join('trac', 'locale', name,
                                           'LC_MESSAGES', domain + '.po'))
    return sorted(name for name in os.listdir(os.path.join('trac', 'locale'))
                       if has_pofile(name))


def main():
    """Merge translated strings from another PO file.

    $ src=../trac-1.2-stable/trac/locale/de/LC_MESSAGES
    $ PYTHONPATH=. contrib/%(prog)s messages $src/messages.po [locale]
    """
    domains = _get_domains()
    if not domains:
        raise ScriptError('No trac/locale/*.pot files.')
    parser = argparse.ArgumentParser(usage=main.__doc__)
    parser.add_argument('domain', choices=domains,
                        help="Name of catalog to merge")
    parser.add_argument('pofile', help="Path of the catalog to merge from")
    parser.add_argument('locale', help="Locale of the catalog to merge from",
                        nargs='?', default=None)
    args = parser.parse_args()

    domain, source_file, locale = args.domain, args.pofile, args.locale
    locales = _get_locales(domain)
    if not locales:
        raise ScriptError('No trac/locale/*/LC_MESSAGES/*.po files.')
    pot = _open_pofile(os.path.join('trac', 'locale', domain + '.pot'))
    source = _open_pofile(source_file)
    if locale:
        preferred_locales = [locale]
    else:
        preferred_locales = [value.split(None, 1)[0]
                             for value in (source.locale and str(source.locale),
                                           source.language_team)
                             if value]
    locale = negotiate_locale(preferred_locales, locales)
    if not locale or locale == 'en_US':
        raise ScriptError('No available *.po file for %s.\n' %
                          ', '.join(preferred_locales))
    target_file = os.path.join('trac', 'locale', locale, 'LC_MESSAGES',
                               domain + '.po')
    target = _open_pofile(target_file)
    pot = _open_pofile(os.path.join('trac', 'locale', domain + '.pot'))
    n = 0
    for source_msg in source:
        msgid = source_msg.id
        if msgid == '':
            continue
        if not _has_msgstr(source_msg):
            continue
        if msgid in target:
            target_msg = target[msgid]
        elif msgid in pot:
            target_msg = pot[msgid]
        else:
            continue
        if target_msg.string == source_msg.string:
            continue
        if not _has_msgstr(source_msg):
            continue
        if _has_msgstr(target_msg) and not _is_fuzzy(target_msg):
            continue
        if msgid not in target:
            target_msg = target_msg.clone()
            target[msgid] = target_msg
        target_msg.string = source_msg.string
        target_msg.flags = source_msg.flags
        n += 1
    if n > 0:
        target.msgid_bugs_address = pot.msgid_bugs_address
        target.revision_date = datetime.utcnow()
        target.locale = locale
        target.language_team = '%s <%s>' % (locale, pot.msgid_bugs_address)
        target.fuzzy = False  # clear fuzzy flag of the header
        with open(target_file, 'w', encoding='utf-8') as f:
            write_po(f, target)
            del f
        print('Merged %d messages from %s and updated %s' % (n, source_file,
                                                             target_file))
    else:
        print('Merged no messages from %s' % source_file)


if __name__ == '__main__':
    rc = 0
    try:
        main()
    except ScriptError as e:
        rc = 1
        sys.stderr.write('%s\n' % e)
    sys.exit(rc)
