# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at https://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at https://trac.edgewall.org/log/.

import unittest

from trac.admin.web_ui import AdminModule
from trac.core import Component, implements
from trac.test import EnvironmentStub, MockRequest
from trac.versioncontrol.api import DbRepositoryProvider, IRepositoryConnector
from trac.versioncontrol.admin import RepositoryAdminPanel
from trac.web.api import RequestDone


class RepositoryAdminPanelTestCase(unittest.TestCase):

    RepositoryConnector = None

    @classmethod
    def setUpClass(cls):
        class RepositoryConnector(Component):
            implements(IRepositoryConnector)

            def get_supported_types(self):
                yield 'RepositoryConnector', 1

            def get_repository(self, repos_type, repos_dir, params):
                pass

        cls.RepositoryConnector = RepositoryConnector

    def setUp(self):
        self.env = EnvironmentStub(enable=('trac.versioncontrol.admin.*',))

    def tearDown(self):
        self.env.reset_db()

    @classmethod
    def tearDownClass(cls):
        from trac.core import ComponentMeta
        ComponentMeta.deregister(cls.RepositoryConnector)

    def test_panel_not_exists_when_no_repository_connectors(self):
        """Repositories admin panel is not present when there are
        no repository connectors enabled.
        """
        req = MockRequest(self.env)
        rap = RepositoryAdminPanel(self.env)
        panels = [panel for panel in rap.get_admin_panels(req)]

        self.assertEqual(0, len(panels))

    def test_panel_exists_when_repository_connectors(self):
        """Repositories admin panel is present when there are
        repository connectors enabled.
        """
        self.env.enable_component(self.RepositoryConnector)
        req = MockRequest(self.env)
        rap = RepositoryAdminPanel(self.env)
        panels = [panel for panel in rap.get_admin_panels(req)]

        self.assertEqual(1, len(panels))


class VersionControlAdminTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()

    def tearDown(self):
        self.env.reset_db()

    def test_render_admin_with_alias_to_default_repos(self):
        with self.env.db_transaction as db:
            # Add aliases to non-existent default repository
            db.executemany(
                "INSERT INTO repository (id, name, value) VALUES (%s, %s, %s)",
                [(1, 'name', ''),     (1, 'dir', None), (1, 'alias', ''),
                 (2, 'name', 'blah'), (2, 'dir', None), (2, 'alias', '')])

        panel = RepositoryAdminPanel(self.env)
        req = MockRequest(self.env)
        template, data = panel.render_admin_panel(req, 'versioncontrol',
                                                  'repository', '')
        repositories = data['repositories']
        self.assertNotEqual({}, repositories)
        self.assertEqual('', repositories['']['name'])
        self.assertEqual('', repositories['']['alias'])
        self.assertEqual('blah', repositories['blah']['name'])
        self.assertEqual('', repositories['blah']['alias'])

    def _add_repository(self, name, type_, path):
        req = MockRequest(
                self.env, method='POST',
                path_info='/admin/versioncontrol/repository',
                args={
                    'add_repos': 'Add',
                    'dir': path,
                    'name': name,
                    'type': type_,
                })

        mod = AdminModule(self.env)
        self.assertTrue(mod.match_request(req))
        with self.assertRaises(RequestDone):
            mod.process_request(req)

        return req

    def _get_repositories(self):
        req = MockRequest(
                self.env, method='GET',
                path_info='/admin/versioncontrol/repository')

        mod = AdminModule(self.env)
        self.assertTrue(mod.match_request(req))
        data = mod.process_request(req)[1]

        return data

    def assert_repository_added(self, req):
        self.assertEqual([], req.chrome['warnings'])
        self.assertEqual(['303 See Other'], req.status_sent)
        self.assertEqual(
                'http://example.org/trac.cgi/admin/versioncontrol/repository',
                req.headers_sent['Location'])

    def assert_repository_exists(self, name, type_, path, data):
        repositories = data['repositories']
        self.assertEqual(name, repositories[name]['name'])
        self.assertEqual(type_, repositories[name]['type'])
        self.assertEqual(path, repositories[name]['dir'])

    def test_add_repository(self):
        name = 'proj1'
        type_ = ''
        path = '/path/to/repos'
        req = self._add_repository(name, type_, path)
        self.assert_repository_added(req)
        data = self._get_repositories()
        self.assert_repository_exists(name, type_, path, data)

    def test_add_repository_with_spaces(self):
        name = 'proj1'
        type_ = ''
        path = '/path/to/repos'
        req = self._add_repository(' %s ' % name, type_, ' %s ' % path)
        self.assert_repository_added(req)
        data = self._get_repositories()
        self.assert_repository_exists(name, type_, path, data)

    def test_add_repository_with_zwsp(self):
        name = 'proj1'
        type_ = ''
        path = '/path/to/repos'
        req = self._add_repository(u'\u200b%s\u200b' % name, type_,
                                   u'\u200b%s\u200b' % path)
        self.assert_repository_added(req)
        data = self._get_repositories()
        self.assert_repository_exists(name, type_, path, data)

    def test_add_repository_non_absolute_path(self):
        name = 'proj1'
        type_ = ''
        path = 'path/to/repos'
        req = self._add_repository(name, type_, path)
        self.assertEqual(
                ['The repository directory must be an absolute path.'],
                req.chrome['warnings'])
        data = self._get_repositories()
        self.assertEqual({}, data['repositories'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RepositoryAdminPanelTestCase))
    suite.addTest(unittest.makeSuite(VersionControlAdminTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
