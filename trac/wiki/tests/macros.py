# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2019 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at https://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at https://trac.edgewall.org/log/.

from StringIO import StringIO
import os
import tempfile
import unittest

from trac.attachment import Attachment
from trac.config import Option, ListOption, IntOption, BoolOption
from trac.test import locale_en, rmtree
from trac.util.datefmt import datetime_now, format_date, utc
from trac.wiki.model import WikiPage
from trac.wiki.tests import formatter


def add_pages(tc, names):
    now = datetime_now(utc)
    for name in names:
        w = WikiPage(tc.env)
        w.name = name
        w.text = '--'
        w.save('joe', 'the page ' + name, '::1', now)


def add_attachment(tc, realm, id, file):
    attachment = Attachment(tc.env, realm, id)
    attachment.description = "image in %s" % id
    attachment.insert(file, StringIO(''), 0, 2)


# == [[Image]]

def image_setup(tc):
    add_pages(tc, ['page:fr', 'page'])
    tc.env.path = tempfile.mkdtemp(prefix='trac-tempenv-')
    add_attachment(tc, 'wiki', 'page:fr', 'img.png')
    add_attachment(tc, 'wiki', 'page', 'img.png')
    htdocs_location = 'http://assets.example.org/common'
    tc.context.req.chrome['htdocs_location'] = htdocs_location
    tc.env.config.set('trac', 'htdocs_location', htdocs_location)

def image_teardown(tc):
    rmtree(os.path.join(tc.env.path, 'files'))
    os.rmdir(tc.env.path) # there was only 'files' below tc.env.path
    tc.env.reset_db()

# Note: using `« test »` string in the following tests for checking
#       unicode robustness and whitespace support (first space is
#       normal ASCII SPACE, second is Unicode NO-BREAK SPACE).

IMAGE_MACRO_TEST_CASES = u"""
============================== Image, no arguments
[[Image]]
------------------------------

============================== Image, no arguments
[[Image()]]
------------------------------

============================== Image, whitespace argument
[[Image( )]]
------------------------------

============================== Image, ZWSP argument
[[Image(​)]]
------------------------------

============================== source: Image, no other arguments
[[Image(source:« test ».png)]]
------------------------------
<p>
<a style="padding:0; border:none" href="/browser/%C2%AB%20test%C2%A0%C2%BB.png"><img src="/browser/%C2%AB%20test%C2%A0%C2%BB.png?format=raw" alt="source:« test ».png" title="source:« test ».png" /></a>
</p>
------------------------------
[[Image(...)]]
============================== source: Image, inline
[[Image(source:« test ».png, inline)]]
------------------------------
<p>
<a style="padding:0; border:none" href="/browser/%C2%AB%20test%C2%A0%C2%BB.png"><img src="/browser/%C2%AB%20test%C2%A0%C2%BB.png?format=raw" alt="source:« test ».png" title="source:« test ».png" /></a>
</p>
------------------------------
<a style="padding:0; border:none" href="/browser/%C2%AB%20test%C2%A0%C2%BB.png"><img src="/browser/%C2%AB%20test%C2%A0%C2%BB.png?format=raw" alt="source:« test ».png" title="source:« test ».png" /></a>
============================== intertrac:source: Image, no other arguments
[[Image(trac:source:/trunk/doc/images/bkgnd_pattern_« test ».png)]]
------------------------------
<p>
<a style="padding:0; border:none" href="https://trac.edgewall.org/intertrac/source%3A/trunk/doc/images/bkgnd_pattern_%C2%AB%20test%C2%A0%C2%BB.png"><img src="https://trac.edgewall.org/intertrac/source%3A/trunk/doc/images/bkgnd_pattern_%C2%AB%20test%C2%A0%C2%BB.png%3Fformat%3Draw" alt="source:/trunk/doc/images/bkgnd_pattern_« test ».png in The Trac Project" crossorigin="anonymous" title="source:/trunk/doc/images/bkgnd_pattern_« test ».png in The Trac Project" /></a>
</p>
============================== source: Image, nolink
[[Image(source:« test », nolink)]]
------------------------------
<p>
<img src="/browser/%C2%AB%20test%C2%A0%C2%BB?format=raw" alt="source:« test »" title="source:« test »" />
</p>
============================== source: Image, normal args
[[Image(source:« test », align=left, title=Test)]]
------------------------------
<p>
<a style="padding:0; border:none" href="/browser/%C2%AB%20test%C2%A0%C2%BB"><img src="/browser/%C2%AB%20test%C2%A0%C2%BB?format=raw" alt="source:« test »" style="float:left" title="Test" /></a>
</p>
============================== source: Image, size arg
[[Image(source:« test », 30%)]]
------------------------------
<p>
<a style="padding:0; border:none" href="/browser/%C2%AB%20test%C2%A0%C2%BB"><img width="30%" alt="source:« test »" title="source:« test »" src="/browser/%C2%AB%20test%C2%A0%C2%BB?format=raw" /></a>
</p>
============================== source: Image, keyword alignment
[[Image(source:« test », right)]]
------------------------------
<p>
<a style="padding:0; border:none" href="/browser/%C2%AB%20test%C2%A0%C2%BB"><img src="/browser/%C2%AB%20test%C2%A0%C2%BB?format=raw" alt="source:« test »" style="float:right" title="source:« test »" /></a>
</p>
============================== http: Image, nolink
[[Image(http://www.edgewall.com/gfx/shredder_« test ».png, nolink)]]
------------------------------
<p>
<img src="http://www.edgewall.com/gfx/shredder_« test ».png" alt="http://www.edgewall.com/gfx/shredder_« test ».png" crossorigin="anonymous" title="http://www.edgewall.com/gfx/shredder_« test ».png" />
</p>
============================== http: Image, absolute, many ':'
[[Image(http://chart.apis.google.com:80/chart?cht=p3&chd=s:hW&chs=250x100&chl=Héllo|Wôrld, title=Google & Charting, link=)]]
------------------------------
<p>
<img src="http://chart.apis.google.com:80/chart?cht=p3&amp;chd=s:hW&amp;chs=250x100&amp;chl=Héllo|Wôrld" alt="http://chart.apis.google.com:80/chart" crossorigin="anonymous" title="Google &amp; Charting" />
</p>
============================== // Image, server-relative
[[Image(//browser/« test »?format=raw, link=)]]
------------------------------
<p>
<img src="/browser/« test »?format=raw" alt="/browser/« test »" title="/browser/« test »" />
</p>
============================== / Image, project-relative, link to WikiStart
[[Image(/browser/« test »?format=raw, link=wiki:WikiStart)]]
------------------------------
<p>
<a style="padding:0; border:none" href="/wiki/WikiStart"><img src="/browser/%C2%AB%20test%C2%A0%C2%BB?format=raw" alt="/browser/« test »" title="/browser/« test »" /></a>
</p>
============================== Strip unicode white-spaces and ZWSPs (#10668)
[[Image(  ​source:« test ».png　 ​, nolink, 100%　 ​)]]
------------------------------
<p>
<img width="100%" alt="source:« test ».png" title="source:« test ».png" src="/browser/%C2%AB%20test%C2%A0%C2%BB.png?format=raw" />
</p>
============================== Attachments on page with ':' characters (#10562)
[[Image("page:fr":img.png​,nolink)]]
------------------------------
<p>
<img src="/raw-attachment/wiki/page%3Afr/img.png" alt="image in page:fr" title="image in page:fr" />
</p>
============================== htdocs: Image, nolink
[[Image(htdocs:trac_logo.png, nolink)]]
------------------------------
<p>
<img src="/chrome/site/trac_logo.png" alt="trac_logo.png" title="trac_logo.png" />
</p>
============================== shared: Image, nolink
[[Image(shared:trac_logo.png, nolink)]]
------------------------------
<p>
<img src="/chrome/shared/trac_logo.png" alt="trac_logo.png" title="trac_logo.png" />
</p>
==============================
[[Image("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=")]]
------------------------------
<p>
<a style="padding:0; border:none" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII="><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=" alt="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=" title="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=" /></a>
</p>
==============================
[[Image("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=", nolink)]]
------------------------------
<p>
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=" alt="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=" title="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoAQMAAAC2MCouAAAAA1BMVEXLQ0MOAUiXAAAAC0lEQVQIHWMYYQAAAPAAASEIRrcAAAAASUVORK5CYII=" />
</p>
==============================
[[Image(notfound.png, nolink)]]
------------------------------
<p>
<img src="http://assets.example.org/common/attachment.png" alt="No image &#34;notfound.png&#34; attached to WikiStart" crossorigin="anonymous" title="No image &#34;notfound.png&#34; attached to WikiStart" />
</p>
==============================
[[Image(img.png, margin-bottom=-1)]]
------------------------------
<p>
<img src="http://assets.example.org/common/attachment.png" alt="No image &#34;img.png&#34; attached to WikiStart" title="No image &#34;img.png&#34; attached to WikiStart" style="margin-bottom: 1px" crossorigin="anonymous" />
</p>
==============================
[[Image(img.png, margin-bottom=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>margin-bottom=--</tt></strong></div>
</p>
==============================
[[Image(img.png, margin-top=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>margin-top=--</tt></strong></div>
</p>
==============================
[[Image(img.png, margin=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>margin=--</tt></strong></div>
</p>
==============================
[[Image(img.png, margin-left=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>margin-left=--</tt></strong></div>
</p>
==============================
[[Image(img.png, margin-right=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>margin-right=--</tt></strong></div>
</p>
==============================
[[Image(img.png, border=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>border=--</tt></strong></div>
</p>
==============================  # Regression test for #12333
= [[Image]]
------------------------------
<h1 id="Image">[[Image]]</h1>
==============================  Invalid use of attachment TracLink
[[Image(attachment:img.png:wiki:page)]]
------------------------------
<p>
</p><div class="system-message"><strong>No filespec given</strong></div><p>
</p>
==============================  Non-existent attachment
[[Image(wiki:page:img2.png)]]
------------------------------
<p>
<img src="http://assets.example.org/common/attachment.png" alt="No image &#34;img2.png&#34; attached to page" crossorigin="anonymous" title="No image &#34;img2.png&#34; attached to page" />
</p>
"""

# Note: in the <img> src attribute above, the Unicode characters
#       within the URI sometimes come out as %-encoded, sometimes raw
#       (server-relative case). Both forms are valid (at least
#       according to the W3C XHTML validator).


# == [[InterTrac]]

def intertrac_setup(tc):
    tc.env.config.set('intertrac', 'example', 'example2')
    # Definition conflict with alias, but must not raise a TypeError.
    tc.env.config.set('intertrac', 'example.url', 'http://example.org')


INTERTRAC_MACRO_TEST_CASES = u"""\
==============================
[[InterTrac]]
------------------------------
<p>
</p><table class="wiki intertrac"><tr><th><em>Prefix</em></th><th><em>Trac Site</em></th></tr><tr><td><strong>example</strong></td><td>Alias for <strong>example2</strong></td></tr><tr><td><a href="https://genshi.edgewall.org/timeline"><strong>genshi</strong></a></td><td><a href="https://genshi.edgewall.org">Genshi\'s Trac</a></td></tr><tr><td><strong>t</strong></td><td>Alias for <strong>trac</strong></td></tr><tr><td><a href="http://trac-hacks.org/timeline"><strong>th</strong></a></td><td><a href="http://trac-hacks.org">Trac Hacks</a></td></tr><tr><td><a href="https://trac.edgewall.org/timeline"><strong>trac</strong></a></td><td><a href="https://trac.edgewall.org">The Trac Project</a></td></tr></table><p>
</p>
"""


# == [[TitleIndex]]

def titleindex_teardown(tc):
    tc.env.reset_db()



TITLEINDEX1_MACRO_TEST_CASES = u"""
============================== TitleIndex, default format
[[TitleIndex()]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
[[TitleIndex]]
============================== TitleIndex, compact format
[[TitleIndex(format=compact)]]
------------------------------
<p>
<a href="/wiki/WikiStart">WikiStart</a>
</p>
------------------------------
[[TitleIndex(...)]]
==============================
[[TitleIndex(min=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>min=--</tt></strong></div>
</p>
==============================
[[TitleIndex(depth=--)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>depth=--</tt></strong></div>
</p>
------------------------------
"""

TITLEINDEX2_MACRO_TEST_CASES = u"""
============================== TitleIndex, default format
[[TitleIndex()]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/WikiEnd">WikiEnd</a></li><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
[[TitleIndex]]
============================== TitleIndex, compact format
[[TitleIndex(format=compact)]]
------------------------------
<p>
<a href="/wiki/WikiEnd">WikiEnd</a>, <a href="/wiki/WikiStart">WikiStart</a>
</p>
------------------------------
[[TitleIndex(...)]]
============================== TitleIndex, default format with prefix
[[TitleIndex(Wiki)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/WikiEnd">WikiEnd</a></li><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
[[TitleIndex(...)]]
============================== TitleIndex, compact format with prefix
[[TitleIndex(Wiki,format=compact)]]
------------------------------
<p>
<a href="/wiki/WikiEnd">WikiEnd</a>, <a href="/wiki/WikiStart">WikiStart</a>
</p>
------------------------------
[[TitleIndex(...)]]
============================== TitleIndex, default format with prefix hidden
[[TitleIndex(Wiki,hideprefix)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/WikiEnd">End</a></li><li><a href="/wiki/WikiStart">Start</a></li></ul></div><p>
</p>
------------------------------
[[TitleIndex(...)]]
============================== TitleIndex, compact format with prefix hidden
[[TitleIndex(Wiki,hideprefix,format=compact)]]
------------------------------
<p>
<a href="/wiki/WikiEnd">End</a>, <a href="/wiki/WikiStart">Start</a>
</p>
------------------------------
[[TitleIndex(...)]]
"""

def titleindex2_setup(tc):
    add_pages(tc, ['WikiEnd'])


TITLEINDEX3_MACRO_TEST_CASES = u"""
============================== TitleIndex, group format
[[TitleIndex(Wiki,format=group)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><strong>Wiki</strong><ul><li><strong>End</strong><ul><li><a href="/wiki/WikiEnd/First">WikiEnd/First</a></li><li><a href="/wiki/WikiEnd/Second">WikiEnd/Second</a></li></ul></li><li><strong>Start</strong><ul><li><a href="/wiki/WikiStart">WikiStart</a></li><li><a href="/wiki/WikiStart/First">WikiStart/First</a></li><li><a href="/wiki/WikiStart/Second">WikiStart/Second</a></li><li><a href="/wiki/WikiStart/Third">WikiStart/Third</a></li></ul></li></ul></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, hierarchy format
[[TitleIndex(WikiStart/, format=hierarchy)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li>WikiStart<ul><li><a href="/wiki/WikiStart/First">First</a></li><li><a href="/wiki/WikiStart/Second">Second</a></li><li><a href="/wiki/WikiStart/Third">Third</a></li></ul></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, group format, prefix hidden
[[TitleIndex(Wiki,hideprefix,format=group)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><strong>End</strong><ul><li><a href="/wiki/WikiEnd/First">End/First</a></li><li><a href="/wiki/WikiEnd/Second">End/Second</a></li></ul></li><li><strong>Start</strong><ul><li><a href="/wiki/WikiStart">Start</a></li><li><a href="/wiki/WikiStart/First">Start/First</a></li><li><a href="/wiki/WikiStart/Second">Start/Second</a></li><li><a href="/wiki/WikiStart/Third">Start/Third</a></li></ul></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, hierarchy format, prefix hidden
[[TitleIndex(WikiStart/,hideprefix,format=hierarchy)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/WikiStart/First">First</a></li><li><a href="/wiki/WikiStart/Second">Second</a></li><li><a href="/wiki/WikiStart/Third">Third</a></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, top-level pages only
[[TitleIndex(depth=0)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
"""

def titleindex3_setup(tc):
    add_pages(tc, [
        'WikiStart/First',
        'WikiStart/Second',
        'WikiStart/Third',
        'WikiEnd/First',
        'WikiEnd/Second',
        ])


TITLEINDEX4_MACRO_TEST_CASES = u"""
============================== TitleIndex group and page with numbers (#7919)
[[TitleIndex(format=group)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><strong>0.11</strong><ul><li><strong>Group</strong><ul><li><a href="/wiki/0.11/GroupOne">0.11/GroupOne</a></li><li><a href="/wiki/0.11/GroupTwo">0.11/GroupTwo</a></li></ul></li><li><a href="/wiki/0.11/Test">0.11/Test</a></li></ul></li><li><strong>Test</strong><ul><li><strong>0.11</strong><ul><li><a href="/wiki/Test0.11/Abc">Test0.11/Abc</a></li><li><a href="/wiki/Test0.11Abc">Test0.11Abc</a></li></ul></li><li><strong>0.12</strong><ul><li><a href="/wiki/Test0.12Def">Test0.12Def</a></li><li><a href="/wiki/Test0.12Ijk">Test0.12Ijk</a></li></ul></li><li><strong>0.13</strong><ul><li><a href="/wiki/Test0.13alpha">Test0.13alpha</a></li><li><a href="/wiki/Test0.13beta">Test0.13beta</a></li></ul></li><li><a href="/wiki/Test0.131">Test0.131</a></li><li><a href="/wiki/Test2">Test2</a></li><li><a href="/wiki/TestTest">TestTest</a></li><li><a href="/wiki/TestThing">TestThing</a></li></ul></li><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, compact format with prefix hidden, including Test0.13*
[[TitleIndex(Test,format=compact,include=*0.13*)]]
------------------------------
<p>
<a href="/wiki/Test0.131">Test0.131</a>, <a href="/wiki/Test0.13alpha">Test0.13alpha</a>, <a href="/wiki/Test0.13beta">Test0.13beta</a>
</p>
------------------------------
============================== TitleIndex, compact format with prefix hidden, including Test0.13* but excluding Test0.131
[[TitleIndex(Test,format=compact,include=*0.13*,exclude=*1)]]
------------------------------
<p>
<a href="/wiki/Test0.13alpha">Test0.13alpha</a>, <a href="/wiki/Test0.13beta">Test0.13beta</a>
</p>
------------------------------
============================== TitleIndex, compact format, excluding various topics
[[TitleIndex(Test,format=compact,exclude=Test0.13*:*0.11*:Test2:Test*i*)]]
------------------------------
<p>
<a href="/wiki/Test0.12Def">Test0.12Def</a>, <a href="/wiki/Test0.12Ijk">Test0.12Ijk</a>, <a href="/wiki/TestTest">TestTest</a>
</p>
------------------------------
============================== TitleIndex, compact format, including and excluding various topics
[[TitleIndex(format=compact,include=*Group*:test2,exclude=*One)]]
------------------------------
<p>
<a href="/wiki/0.11/GroupTwo">0.11/GroupTwo</a>
</p>
------------------------------
"""

def titleindex4_setup(tc):
    add_pages(tc, [
        'TestTest',
        'TestThing',
        'Test2',
        'Test0.11Abc',
        'Test0.11/Abc',
        'Test0.12Def',
        'Test0.12Ijk',
        'Test0.13alpha',
        'Test0.13beta',
        'Test0.131',
        '0.11/Test',
        '0.11/GroupOne',
        '0.11/GroupTwo',
        ])


TITLEINDEX5_MACRO_TEST_CASES = u"""
============================== TitleIndex, hierarchy format with complex hierarchy
[[TitleIndex(format=hierarchy)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/TracDev">TracDev</a><ul><li><a href="/wiki/TracDev/ApiChanges">ApiChanges</a><ul><li><a href="/wiki/TracDev/ApiChanges/0.10">0.10</a></li><li><a href="/wiki/TracDev/ApiChanges/0.11">0.11</a></li><li><a href="/wiki/TracDev/ApiChanges/0.12">0.12</a><ul><li>Missing<ul><li><a href="/wiki/TracDev/ApiChanges/0.12/Missing/Exists">Exists</a></li></ul></li></ul></li></ul></li></ul></li><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, hierarchy format with complex hierarchy (and min=5)
[[TitleIndex(format=hierarchy,min=5)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><a href="/wiki/TracDev">TracDev</a><ul><li><a href="/wiki/TracDev/ApiChanges">ApiChanges</a></li><li><a href="/wiki/TracDev/ApiChanges/0.10">ApiChanges/0.10</a></li><li><a href="/wiki/TracDev/ApiChanges/0.11">ApiChanges/0.11</a></li><li><a href="/wiki/TracDev/ApiChanges/0.12">ApiChanges/0.12</a></li><li><a href="/wiki/TracDev/ApiChanges/0.12/Missing/Exists">ApiChanges/0.12/Missing/Exists</a></li></ul></li><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
============================== TitleIndex, group format with complex hierarchy
[[TitleIndex(format=group)]]
------------------------------
<p>
</p><div class="titleindex"><ul><li><strong>TracDev</strong><ul><li><a href="/wiki/TracDev">TracDev</a></li><li><strong>ApiChanges</strong><ul><li><a href="/wiki/TracDev/ApiChanges">TracDev/ApiChanges</a></li><li><a href="/wiki/TracDev/ApiChanges/0.10">TracDev/ApiChanges/0.10</a></li><li><a href="/wiki/TracDev/ApiChanges/0.11">TracDev/ApiChanges/0.11</a></li><li><strong>0.12</strong><ul><li><a href="/wiki/TracDev/ApiChanges/0.12">TracDev/ApiChanges/0.12</a></li><li><a href="/wiki/TracDev/ApiChanges/0.12/Missing/Exists">TracDev/ApiChanges/0.12/Missing/Exists</a></li></ul></li></ul></li></ul></li><li><a href="/wiki/WikiStart">WikiStart</a></li></ul></div><p>
</p>
------------------------------
"""

def titleindex5_setup(tc):
    add_pages(tc, [
        'TracDev',
        'TracDev/ApiChanges',
        'TracDev/ApiChanges/0.10',
        'TracDev/ApiChanges/0.11',
        'TracDev/ApiChanges/0.12',
        'TracDev/ApiChanges/0.12/Missing/Exists',
        ])


RECENTCHANGES_MACRO_TEST_CASES = u""""
============================== RecentChanges, group option
[[RecentChanges()]]
[[RecentChanges(group=date)]]
[[RecentChanges(group=none)]]
[[RecentChanges(,2,group=none)]]
[[RecentChanges(Wiki,group=none)]]
[[RecentChanges(Wiki,1,group=none)]]
------------------------------
<p>
</p><div><h3>%(date)s</h3><ul><li><a href="/wiki/WikiEnd">WikiEnd</a>
</li><li><a href="/wiki/WikiMid">WikiMid</a>
</li><li><a href="/wiki/WikiStart">WikiStart</a>
</li></ul></div><p>
</p><div><h3>%(date)s</h3><ul><li><a href="/wiki/WikiEnd">WikiEnd</a>
</li><li><a href="/wiki/WikiMid">WikiMid</a>
</li><li><a href="/wiki/WikiStart">WikiStart</a>
</li></ul></div><p>
</p><div><ul><li><a href="/wiki/WikiEnd">WikiEnd</a>
</li><li><a href="/wiki/WikiMid">WikiMid</a>
</li><li><a href="/wiki/WikiStart">WikiStart</a>
</li></ul></div><p>
</p><div><ul><li><a href="/wiki/WikiEnd">WikiEnd</a>
</li><li><a href="/wiki/WikiMid">WikiMid</a>
</li></ul></div><p>
</p><div><ul><li><a href="/wiki/WikiEnd">WikiEnd</a>
</li><li><a href="/wiki/WikiMid">WikiMid</a>
</li><li><a href="/wiki/WikiStart">WikiStart</a>
</li></ul></div><p>
</p><div><ul><li><a href="/wiki/WikiEnd">WikiEnd</a>
</li></ul></div><p>
</p>
==============================
[[RecentChanges(Trac, --)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>--</tt></strong></div>
</p>
------------------------------
"""

def recentchanges_setup(tc):
    def add_pages(tc, names):
        for name in names:
            now = datetime_now(utc)
            w = WikiPage(tc.env)
            w.name = name
            w.text = '--'
            w.save('joe', 'the page ' + name, '::1', now)
    add_pages(tc, [
        'WikiMid',
        'WikiEnd',
        ])
    tc.correct = tc.correct % {'date': format_date(tzinfo=utc,
                                                   locale=locale_en)}

def recentchanges_teardown(tc):
    tc.env.reset_db()


PAGEOUTLINE_MACRO_TEST_CASES = u""""\
==============================
[[PageOutline(a)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>a</tt></strong></div>
</p>
==============================
[[PageOutline(a-b)]]
------------------------------
<p>
<div class="system-message"><strong>Invalid macro argument <tt>a</tt></strong></div>
</p>
==============================
[[PageOutline(0)]]
= Heading Level 1
== Heading Level 2
------------------------------
<p>
</p><div class="wiki-toc">
<ol>
  <li>
    <a href="#HeadingLevel1">Heading Level 1</a>
  </li>
</ol>
</div><p>
</p>
<h1 id="HeadingLevel1">Heading Level 1</h1>
<h2 id="HeadingLevel2">Heading Level 2</h2>
==============================
[[PageOutline(7)]]
===== Heading Level 5
====== Heading Level 6
------------------------------
<p>
</p><div class="wiki-toc">
                    <ol>
                      <li>
                        <a href="#HeadingLevel6">Heading Level 6</a>
                      </li>
                    </ol>
</div><p>
</p>
<h5 id="HeadingLevel5">Heading Level 5</h5>
<h6 id="HeadingLevel6">Heading Level 6</h6>
==============================
[[PageOutline(0-7)]]
= Heading Level 1
== Heading Level 2
=== Heading Level 3
==== Heading Level 4
===== Heading Level 5
====== Heading Level 6
------------------------------
<p>
</p><div class="wiki-toc">
<ol>
  <li>
    <a href="#HeadingLevel1">Heading Level 1</a>
    <ol>
      <li>
        <a href="#HeadingLevel2">Heading Level 2</a>
        <ol>
          <li>
            <a href="#HeadingLevel3">Heading Level 3</a>
            <ol>
              <li>
                <a href="#HeadingLevel4">Heading Level 4</a>
                <ol>
                  <li>
                    <a href="#HeadingLevel5">Heading Level 5</a>
                    <ol>
                      <li>
                        <a href="#HeadingLevel6">Heading Level 6</a>
                      </li>
                    </ol>
                  </li>
                </ol>
              </li>
            </ol>
          </li>
        </ol>
      </li>
    </ol>
  </li>
</ol>
</div><p>
</p>
<h1 id="HeadingLevel1">Heading Level 1</h1>
<h2 id="HeadingLevel2">Heading Level 2</h2>
<h3 id="HeadingLevel3">Heading Level 3</h3>
<h4 id="HeadingLevel4">Heading Level 4</h4>
<h5 id="HeadingLevel5">Heading Level 5</h5>
<h6 id="HeadingLevel6">Heading Level 6</h6>
"""


TRACINI_MACRO_TEST_CASES = u"""\
============================== TracIni, option with empty doc (#10940)
[[TracIni(section-42)]]
------------------------------
<p>
</p><div class="tracini"><h3 id="section-42-section"><code>[section-42]</code></h3>\
<table class="wiki"><tbody>\
<tr class="even"><td><tt>option1</tt></td><td></td><td class="default"><code>value</code></td></tr>\
<tr class="odd"><td><tt>option2</tt></td><td><p>
blah
</p>
</td><td class="default"><code>value</code></td></tr></tbody></table></div><p>
</p>
------------------------------
============================== TracIni, list option with sep=| (#11074)
[[TracIni(section-list)]]
------------------------------
<p>
</p><div class="tracini">\
<h3 id="section-list-section"><code>[section-list]</code></h3>\
<table class="wiki"><tbody>\
<tr class="even"><td><tt>option1</tt></td><td></td><td class="default"><code>4.2|42|42||0|enabled</code></td></tr>\
</tbody></table>\
</div><p>
</p>
------------------------------
============================== TracIni, option with "false" value as default
[[TracIni(section-def)]]
------------------------------
<p>
</p><div class="tracini">\
<h3 id="section-def-section"><code>[section-def]</code></h3>\
<table class="wiki"><tbody>\
<tr class="even"><td><tt>option1</tt></td><td></td><td class="nodefault">(no default)</td></tr>\
<tr class="odd"><td><tt>option2</tt></td><td></td><td class="nodefault">(no default)</td></tr>\
<tr class="even"><td><tt>option3</tt></td><td></td><td class="default"><code>0</code></td></tr>\
<tr class="odd"><td><tt>option4</tt></td><td></td><td class="default"><code>disabled</code></td></tr>\
<tr class="even"><td><tt>option5</tt></td><td></td><td class="default"><code></code></td></tr>\
</tbody></table>\
</div><p>
</p>
------------------------------
"""

def tracini_setup(tc):
    tc._orig_registry = Option.registry
    class Foo(object):
        option_a1 = (Option)('section-42', 'option1', 'value', doc='')
        option_a2 = (Option)('section-42', 'option2', 'value', doc='blah')
        option_l1 = (ListOption)('section-list', 'option1',
                                 [4.2, '42', 42, None, 0, True], sep='|')
        option_d1 = (Option)('section-def', 'option1', None)
        option_d2 = (Option)('section-def', 'option2', '')
        option_d3 = (IntOption)('section-def', 'option3', 0)
        option_d4 = (BoolOption)('section-def', 'option4', False)
        option_d5 = (ListOption)('section-def', 'option5', [])

def tracini_teardown(tc):
    Option.registry = tc._orig_registry


def suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(IMAGE_MACRO_TEST_CASES, file=__file__,
                                  setup=image_setup,
                                  teardown=image_teardown))
    suite.addTest(formatter.suite(INTERTRAC_MACRO_TEST_CASES, file=__file__,
                                  setup=intertrac_setup))
    suite.addTest(formatter.suite(TITLEINDEX1_MACRO_TEST_CASES, file=__file__))
    suite.addTest(formatter.suite(TITLEINDEX2_MACRO_TEST_CASES, file=__file__,
                                  setup=titleindex2_setup,
                                  teardown=titleindex_teardown))
    suite.addTest(formatter.suite(TITLEINDEX3_MACRO_TEST_CASES, file=__file__,
                                  setup=titleindex3_setup,
                                  teardown=titleindex_teardown))
    suite.addTest(formatter.suite(TITLEINDEX4_MACRO_TEST_CASES, file=__file__,
                                  setup=titleindex4_setup,
                                  teardown=titleindex_teardown))
    suite.addTest(formatter.suite(TITLEINDEX5_MACRO_TEST_CASES, file=__file__,
                                  setup=titleindex5_setup,
                                  teardown=titleindex_teardown))
    suite.addTest(formatter.suite(RECENTCHANGES_MACRO_TEST_CASES, file=__file__,
                                  setup=recentchanges_setup,
                                  teardown=recentchanges_teardown))
    suite.addTest(formatter.suite(PAGEOUTLINE_MACRO_TEST_CASES, file=__file__))
    suite.addTest(formatter.suite(TRACINI_MACRO_TEST_CASES, file=__file__,
                                  setup=tracini_setup,
                                  teardown=tracini_teardown))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
