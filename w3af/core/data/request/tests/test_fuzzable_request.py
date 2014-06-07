# -*- coding: utf-8 -*-
"""
test_fuzzablerequest.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.kv_container import KeyValueContainer
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.dc.form import Form


@attr('smoke')
class TestFuzzableRequest(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://w3af.com/a/b/c.php')

    def test_variants_commutative(self):
        # 'is_variant_of' is commutative
        fr = FuzzableRequest(self.url, method='POST', post_data={'a': ['1']})
        fr_other = FuzzableRequest(self.url, method='POST', post_data={'a': ['1']})
        self.assertTrue(fr.is_variant_of(fr_other))
        self.assertTrue(fr_other.is_variant_of(fr))

    def test_variants_false_diff_meths(self):
        # Different methods
        fr_get = FuzzableRequest(self.url, method='GET', post_data={'a': ['1']})
        fr_post = FuzzableRequest(self.url, method='POST', post_data={'a': ['1']})
        self.assertFalse(fr_get.is_variant_of(fr_post))

    def test_variants_false_diff_params_type(self):
        fr = FuzzableRequest(
            self.url, method='GET', post_data={'a': ['1'], 'b': ['1']})
        fr_other = FuzzableRequest(
            self.url, method='GET', post_data={'a': ['2'], 'b': ['cc']})
        self.assertFalse(fr.is_variant_of(fr_other))

    def test_variants_false_nonetype_in_params(self):
        fr = FuzzableRequest(self.url, method='GET', post_data={'a': [None]})
        fr_other = FuzzableRequest(self.url, method='GET', post_data={'a': ['s']})
        self.assertFalse(fr.is_variant_of(fr_other))

    def test_variants_true_similar_params(self):
        # change the url by adding a querystring. shouldn't affect anything.
        url = self.url.url_join('?a=z')
        fr = FuzzableRequest(url, method='GET', post_data={'a': ['1'], 'b': ['bb']})
        fr_other = FuzzableRequest(
            self.url, method='GET', post_data={'a': ['2'], 'b': ['cc']})
        self.assertTrue(fr.is_variant_of(fr_other))

    def test_variants_true_similar_params_two(self):
        fr = FuzzableRequest(self.url, method='GET', post_data={'a': ['b']})
        fr_other = FuzzableRequest(self.url, method='GET', post_data={'a': ['']})
        self.assertTrue(fr.is_variant_of(fr_other))

    def test_dump_case01(self):
        expected = '\r\n'.join(['GET http://w3af.com/a/b/c.php HTTP/1.1',
                                'Hello: World',
                                '',
                                ''])
        headers = Headers([('Hello', 'World')])

        #TODO: Note that I'm passing a dc to the FuzzableRequest and it's not
        # appearing in the dump. It might be a bug...
        fr = FuzzableRequest(self.url, method='GET', post_data={'a': ['b']},
                             headers=headers)
        self.assertEqual(fr.dump(), expected)

    def test_dump_case02(self):
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: Múndo',
                                 u'',
                                 u''])
        headers = Headers([(u'Hola', u'Múndo')])
        
        #TODO: Note that I'm passing a dc to the FuzzableRequest and it's not
        # appearing in the dump. It might be a bug...
        fr = FuzzableRequest(self.url, method='GET', post_data={u'á': ['b']},
                             headers=headers)
        self.assertEqual(fr.dump(), expected.encode('utf-8'))

    def test_dump_case03(self):
        header_value = ''.join(chr(i) for i in xrange(256))
        
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: %s' % smart_unicode(header_value),
                                 u'',
                                 u''])

        headers = Headers([(u'Hola', header_value)])
        
        #TODO: Note that I'm passing a dc to the FuzzableRequest and it's not
        # appearing in the dump. It might be a bug...
        fr = FuzzableRequest(self.url, method='GET', post_data={u'a': ['b']},
                             headers=headers)
        self.assertEqual(fr.dump(), expected)

    def test_dump_mangle(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"),\
                             headers=Headers([('Host','www.w3af.com'),]))

        expected = u'\r\n'.join([u'GET http://www.w3af.com/ HTTP/1.1',
                                 u'Host: www.w3af.com',
                                 u'',
                                 u''])
        
        self.assertEqual(fr.dump(), expected)
        
        fr.set_method('POST')
        fr.set_data('data=23')
        
        expected = u'\r\n'.join([u'POST http://www.w3af.com/ HTTP/1.1',
                                 u'Host: www.w3af.com',
                                 u'',
                                 u'data=23'])
        
        self.assertEqual(fr.dump(), expected)

    def test_export_without_post_data(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"))
        self.assertEqual(fr.export(), '"GET","http://www.w3af.com/",""')
    
    def test_export_with_post_data(self):
        dc = KeyValueContainer(init_val=[('a', ['1'])])
        fr = FuzzableRequest(URL("http://www.w3af.com/"), post_data=dc)

        self.assertEqual(fr.export(), '"GET","http://www.w3af.com/","a=1"')
        
    def test_equal(self):
        u = URL("""http://www.w3af.com/""")
        fr1 = FuzzableRequest(u)
        fr2 = FuzzableRequest(u)
        self.assertEqual(fr1, fr2)

        fr1 = FuzzableRequest(URL("http://www.w3af.com/a"))
        fr2 = FuzzableRequest(URL("http://www.w3af.com/b"))
        self.assertNotEqual(fr1, fr2)
        
        fr1 = FuzzableRequest(u)
        fr2 = FuzzableRequest(u, method='POST')
        self.assertNotEqual(fr1, fr2)
    
    def test_set_url(self):
        self.assertRaises(TypeError, FuzzableRequest, 'http://www.google.com/')
        
        url = URL('http://www.google.com/')
        r = FuzzableRequest(url)
        self.assertEqual(r.get_url(), url)

    def test_str(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"))
        self.assertEqual(str(fr), 'http://www.w3af.com/ | Method: GET')

        self.assertEqual(repr(fr),
                         '<fuzzable request | GET | http://www.w3af.com/>')

        fr.set_method('TRACE')
        self.assertEqual(str(fr), 'http://www.w3af.com/ | Method: TRACE')

    def test_sent_url(self):
        f = FuzzableRequest(URL('''http://example.com/a?p=d'z"0&paged=2'''))
        self.assertTrue(f.sent('d%5C%27z%5C%220'))

        f = FuzzableRequest(URL('http://example.com/a?p=<SCrIPT>alert("bsMs")</SCrIPT>'))
        self.assertTrue(f.sent('<SCrIPT>alert(\"bsMs\")</SCrIPT>'))

        f = FuzzableRequest(URL('http://example.com/?p=<ScRIPT>a=/PlaO/%0Afake_alert(a.source)</SCRiPT>'))
        self.assertTrue(f.sent('<ScRIPT>a=/PlaO/fake_alert(a.source)</SCRiPT>'))

    def test_sent_post_data(self):
        form = Form()
        form.add_input([("name", "username"), ("value", """d'z"0""")])
        form.add_input([("name", "address"), ("value", "")])

        f = FuzzableRequest(URL('http://example.com/'), post_data=form)
        self.assertTrue(f.sent('d%5C%27z%5C%220'))
