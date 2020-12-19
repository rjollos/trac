# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2020 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at https://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at https://trac.edgewall.org/log/.

import os.path
import textwrap
import unittest

from trac.config import ConfigurationError
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock, mkdtemp, rmtree
from trac.util import create_file
from trac.versioncontrol.api import RepositoryManager
from trac.versioncontrol.svn_authz import AuthzSourcePolicy, parse


class AuthzParserTestCase(unittest.TestCase):

    def setUp(self):
        self.tmpdir = mkdtemp()
        self.authz_file = os.path.join(self.tmpdir, 'trac-authz')

    def tearDown(self):
        rmtree(self.tmpdir)

    def test_parse_file(self):
        create_file(self.authz_file, textwrap.dedent("""\
            [groups]
            developers = foo, bar
            users = @developers, &baz

            [aliases]
            baz = CN=Hàröld Hacker,OU=Enginéers,DC=red-bean,DC=com

            # Applies to all repositories
            [/]
            * = r

            [/trunk]
            @developers = rw
            &baz =
            @users = r

            [/branches]
            bar = rw

            ; Applies only to module
            [module:/trunk]
            foo = rw
            &baz = r

            ; Unicode module names
            [module:/c/résumé]
            bar = rw
            Foo = rw
            BAZ = r

            ; Unused module, not parsed
            [unused:/some/path]
            foo = r
            """))
        authz = parse(self.authz_file, {'', 'module'})
        self.assertEqual({
            '': {
                '/': {
                    '*': True,
                },
                '/trunk': {
                    'foo': True,
                    'bar': True,
                    'CN=Hàröld Hacker,OU=Enginéers,DC=red-bean,DC=com': True,
                },
                '/branches': {
                    'bar': True,
                },
            },
            'module': {
                '/trunk': {
                    'foo': True,
                    'CN=Hàröld Hacker,OU=Enginéers,DC=red-bean,DC=com': True,
                },
                '/c/résumé': {
                    'bar': True,
                    'Foo': True,
                    'BAZ': True,
                },
            },
        }, authz)


class AuthzSourcePolicyTestCase(unittest.TestCase):

    def setUp(self):
        tmpdir = mkdtemp()
        self.authz_file = os.path.join(tmpdir, 'trac-authz')
        create_file(self.authz_file, textwrap.dedent("""\
            [groups]
            group1 = user
            group2 = @group1

            cycle1 = @cycle2
            cycle2 = @cycle3
            cycle3 = @cycle1, user

            alias1 = &jekyll
            alias2 = @alias1

            [aliases]
            jekyll = Mr Hyde

            # Read / write permissions
            [/readonly]
            user = r
            [/writeonly]
            user = w
            [/readwrite]
            user = rw
            [/empty]
            user =

            # Trailing slashes
            [/trailing_a]
            user = r
            [/trailing_b/]
            user = r

            # Sub-paths
            [/sub/path]
            user = r

            # Module usage
            [module:/module_a]
            user = r
            [other:/module_b]
            user = r
            [/module_c]
            user = r
            [module:/module_d]
            user =
            [/module_d]
            user = r

            # Wildcards
            [/wildcard]
            * = r

            # Special tokens
            [/special/anonymous]
            $anonymous = r
            [/special/authenticated]
            $authenticated = r

            # Groups
            [/groups_a]
            @group1 = r
            [/groups_b]
            @group2 = r
            [/cyclic]
            @cycle1 = r

            # Precedence
            [module:/precedence_a]
            user =
            [/precedence_a]
            user = r
            [/precedence_b]
            user = r
            [/precedence_b/sub]
            user =
            [/precedence_b/sub/test]
            user = r
            [/precedence_c]
            user =
            @group1 = r
            [/precedence_d]
            @group1 = r
            user =

            # Aliases
            [/aliases_a]
            &jekyll = r
            [/aliases_b]
            @alias2 = r

            # Scoped repository
            [scoped:/scope/dir1]
            joe = r
            [scoped:/scope/dir2]
            Jane = r

            # multiple entries
            [/multiple]
            $authenticated = r
            [/multiple/foo]
            joe =
            $authenticated =
            * = r
            [/multiple/bar]
            * =
            john = r
            Jane = r
            $anonymous = r
            [/multiple/baz]
            $anonymous = r
            * =
            Jane = r
            [module:/multiple/bar]
            joe = r
            john =

            # multiple entries with module and parent directory
            [/multiple/1]
            user = r
            @group1 = r
            $authenticated = r
            * = r
            [module:/multiple/1/user]
            user =
            [module:/multiple/1/group]
            @group1 =
            [module:/multiple/1/auth]
            $authenticated =
            [module:/multiple/1/star]
            * =
            [/multiple/2]
            user =
            @group1 =
            $authenticated =
            * =
            [module:/multiple/2/user]
            user = r
            [module:/multiple/2/group]
            @group1 = r
            [module:/multiple/2/auth]
            $authenticated = r
            [module:/multiple/2/star]
            * = r
            """))
        self.env = EnvironmentStub(enable=[AuthzSourcePolicy], path=tmpdir)
        self.env.config.set('trac', 'permission_policies',
                            'AuthzSourcePolicy, DefaultPermissionPolicy')
        self.env.config.set('svn', 'authz_file', self.authz_file)

        # Monkey-subclass RepositoryManager to serve mock repositories
        rm = RepositoryManager(self.env)

        class TestRepositoryManager(rm.__class__):
            def get_real_repositories(self):
                return {Mock(reponame='module'), Mock(reponame='other'),
                        Mock(reponame='scoped')}

            def get_repository(self, reponame):
                if reponame == 'scoped':
                    def get_changeset(rev):
                        if rev == 123:
                            def get_changes():
                                yield ('/dir1/file',)
                        elif rev == 456:
                            def get_changes():
                                yield ('/dir2/file',)
                        else:
                            def get_changes():
                                return iter([])
                        return Mock(get_changes=get_changes)
                    return Mock(scope='/scope',
                                get_changeset=get_changeset)
                return Mock(scope='/')

        rm.__class__ = TestRepositoryManager

    def tearDown(self):
        self.env.reset_db_and_disk()

    def test_get_authz_file_notfound_raises(self):
        """ConfigurationError exception is raised if file not found."""
        authz_file = os.path.join(self.env.path, 'some-nonexistent-file')
        self.env.config.set('svn', 'authz_file', authz_file)
        policy = AuthzSourcePolicy(self.env)
        self.assertRaises(ConfigurationError, policy.check_permission,
                          'BROWSER_VIEW', 'user', None, None)

    def test_get_authz_file_notdefined_raises(self):
        """ConfigurationError exception is raised if the option
        `[svn] authz_file` is not specified in trac.ini."""
        self.env.config.remove('svn', 'authz_file')
        policy = AuthzSourcePolicy(self.env)
        self.assertRaises(ConfigurationError, policy.check_permission,
                          'BROWSER_VIEW', 'user', None, None)

    def test_get_authz_file_empty_raises(self):
        """ConfigurationError exception is raised if the option
        `[svn] authz_file` is empty."""
        self.env.config.set('svn', 'authz_file', '')
        policy = AuthzSourcePolicy(self.env)
        self.assertRaises(ConfigurationError, policy.check_permission,
                          'BROWSER_VIEW', 'user', None, None)

    def test_get_authz_file_removed_raises(self):
        """ConfigurationError exception is raised if file is removed."""
        policy = AuthzSourcePolicy(self.env)
        os.remove(self.authz_file)
        self.assertRaises(ConfigurationError, policy.check_permission,
                          'BROWSER_VIEW', 'user', None, None)

    def test_parse_error_raises(self):
        """ConfigurationError exception is raised when exception occurs
        parsing the `[svn authz_file`."""
        create_file(self.authz_file, textwrap.dedent("""\
            [/somepath
            joe = r
            """))
        policy = AuthzSourcePolicy(self.env)
        self.assertRaises(ConfigurationError, policy.check_permission,
                          'BROWSER_VIEW', 'user', None, None)

    def assertPathPerm(self, result, user, reponame=None, path=None):
        """Assert that `user` is granted access `result` to `path` within
        the repository `reponame`.
        """
        policy = AuthzSourcePolicy(self.env)
        resource = None
        if reponame is not None:
            resource = Resource('source', path,
                                parent=Resource('repository', reponame))
        for perm in ('BROWSER_VIEW', 'FILE_VIEW', 'LOG_VIEW'):
            check = policy.check_permission(perm, user, resource, None)
            self.assertEqual(result, check)

    def assertRevPerm(self, result, user, reponame=None, rev=None):
        """Assert that `user` is granted access `result` to `rev` within
        the repository `reponame`.
        """
        policy = AuthzSourcePolicy(self.env)
        resource = None
        if reponame is not None:
            resource = Resource('changeset', rev,
                                parent=Resource('repository', reponame))
        check = policy.check_permission('CHANGESET_VIEW', user, resource,
                                             None)
        self.assertEqual(result, check)

    def test_coarse_permissions(self):
        policy = AuthzSourcePolicy(self.env)
        # Granted to all due to wildcard
        self.assertPathPerm(True, 'unknown')
        self.assertPathPerm(True, 'joe')
        self.assertRevPerm(True, 'unknown')
        self.assertRevPerm(True, 'joe')
        # Granted if at least one fine permission is granted
        policy._mtime = 0
        create_file(self.authz_file, textwrap.dedent("""\
            [/somepath]
            joe = r
            denied =
            [module:/otherpath]
            Jane = r
            $anonymous = r
            [inactive:/not-in-this-instance]
            unknown = r
            """))
        self.assertPathPerm(None, 'unknown')
        self.assertRevPerm(None, 'unknown')
        self.assertPathPerm(None, 'denied')
        self.assertRevPerm(None, 'denied')
        self.assertPathPerm(True, 'joe')
        self.assertRevPerm(True, 'joe')
        self.assertPathPerm(True, 'Jane')
        self.assertRevPerm(True, 'Jane')
        self.assertPathPerm(True, 'anonymous')
        self.assertRevPerm(True, 'anonymous')

    def test_default_permission(self):
        # By default, permissions are undecided
        self.assertPathPerm(None, 'joe', '', '/not_defined')
        self.assertPathPerm(None, 'Jane', 'repo', '/not/defined/either')

    def test_read_write(self):
        # Allow 'r' and 'rw' entries, deny 'w' and empty entries
        self.assertPathPerm(True, 'user', '', '/readonly')
        self.assertPathPerm(True, 'user', '', '/readwrite')
        self.assertPathPerm(False, 'user', '', '/writeonly')
        self.assertPathPerm(False, 'user', '', '/empty')

    def test_trailing_slashes(self):
        # Combinations of trailing slashes in the file and in the path
        self.assertPathPerm(True, 'user', '', '/trailing_a')
        self.assertPathPerm(True, 'user', '', '/trailing_a/')
        self.assertPathPerm(True, 'user', '', '/trailing_b')
        self.assertPathPerm(True, 'user', '', '/trailing_b/')

    def test_sub_path(self):
        # Permissions are inherited from containing directories
        self.assertPathPerm(True, 'user', '', '/sub/path')
        self.assertPathPerm(True, 'user', '', '/sub/path/test')
        self.assertPathPerm(True, 'user', '', '/sub/path/other/sub')

    def test_module_usage(self):
        # If a module name is specified, the rules are specific to the module
        self.assertPathPerm(True, 'user', 'module', '/module_a')
        self.assertPathPerm(None, 'user', 'module', '/module_b')
        # If a module is specified, but the configuration contains a non-module
        # path, the non-module path can still apply
        self.assertPathPerm(True, 'user', 'module', '/module_c')
        # The module-specific rule takes precedence
        self.assertPathPerm(True, 'user', '', '/module_d')
        self.assertPathPerm(False, 'user', 'module', '/module_d')

    def test_wildcard(self):
        # The * wildcard matches all users, including anonymous
        self.assertPathPerm(True, 'anonymous', '', '/wildcard')
        self.assertPathPerm(True, 'joe', '', '/wildcard')
        self.assertPathPerm(True, 'Jane', '', '/wildcard')

    def test_special_tokens(self):
        # The $anonymous token matches only anonymous users
        self.assertPathPerm(True, 'anonymous', '', '/special/anonymous')
        self.assertPathPerm(None, 'user', '', '/special/anonymous')
        # The $authenticated token matches all authenticated users
        self.assertPathPerm(None, 'anonymous', '', '/special/authenticated')
        self.assertPathPerm(True, 'joe', '', '/special/authenticated')
        self.assertPathPerm(True, 'Jane', '', '/special/authenticated')

    def test_groups(self):
        # Groups are specified in a separate section and used with an @ prefix
        self.assertPathPerm(True, 'user', '', '/groups_a')
        # Groups can also be members of other groups
        self.assertPathPerm(True, 'user', '', '/groups_b')
        # Groups should not be defined cyclically, but they are still handled
        # correctly to avoid infinite loops
        self.assertPathPerm(True, 'user', '', '/cyclic')

    def test_precedence(self):
        # Module-specific sections take precedence over non-module sections
        self.assertPathPerm(False, 'user', 'module', '/precedence_a')
        # The most specific section applies
        self.assertPathPerm(True, 'user', '', '/precedence_b/sub/test')
        # ... intentional deviation from SVN's rules as we need to
        # make '/precedence_b/sub' browseable so that the user can see
        # '/precedence_b/sub/test':
        self.assertPathPerm(True, 'user', '', '/precedence_b/sub')
        self.assertPathPerm(True, 'user', '', '/precedence_b')
        # Ordering isn't significant; any entry could grant permission
        self.assertPathPerm(True, 'user', '', '/precedence_c')
        self.assertPathPerm(True, 'user', '', '/precedence_d')

    def test_aliases(self):
        # Aliases are specified in a separate section and used with an & prefix
        self.assertPathPerm(True, 'Mr Hyde', '', '/aliases_a')
        # Aliases can also be used in groups
        self.assertPathPerm(True, 'Mr Hyde', '', '/aliases_b')

    def test_scoped_repository(self):
        # Take repository scope into account
        self.assertPathPerm(True, 'joe', 'scoped', '/dir1')
        self.assertPathPerm(None, 'joe', 'scoped', '/dir2')
        self.assertPathPerm(True, 'joe', 'scoped', '/')
        self.assertPathPerm(None, 'Jane', 'scoped', '/dir1')
        self.assertPathPerm(True, 'Jane', 'scoped', '/dir2')
        self.assertPathPerm(True, 'Jane', 'scoped', '/')

    def test_multiple_entries(self):
        self.assertPathPerm(True,  'anonymous', '',       '/multiple/foo')
        self.assertPathPerm(True,  'joe',       '',       '/multiple/foo')
        self.assertPathPerm(True,  'anonymous', '',       '/multiple/bar')
        self.assertPathPerm(False, 'joe',       '',       '/multiple/bar')
        self.assertPathPerm(True,  'john',      '',       '/multiple/bar')
        self.assertPathPerm(True,  'anonymous', '',       '/multiple/baz')
        self.assertPathPerm(True,  'Jane',      '',       '/multiple/baz')
        self.assertPathPerm(False, 'joe',       '',       '/multiple/baz')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/foo')
        self.assertPathPerm(True,  'joe',       'module', '/multiple/foo')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/bar')
        self.assertPathPerm(True,  'joe',       'module', '/multiple/bar')
        self.assertPathPerm(False, 'john',      'module', '/multiple/bar')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/baz')
        self.assertPathPerm(True,  'Jane',      'module', '/multiple/baz')
        self.assertPathPerm(False, 'joe',       'module', '/multiple/baz')

    def test_multiple_entries_with_module_and_parent_directory(self):
        self.assertPathPerm(True,  'anonymous', '',       '/multiple/1')
        self.assertPathPerm(True,  'user',      '',       '/multiple/1')
        self.assertPathPerm(True,  'someone',   '',       '/multiple/1')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/1')
        self.assertPathPerm(True,  'user',      'module', '/multiple/1')
        self.assertPathPerm(True,  'someone',   'module', '/multiple/1')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/1/user')
        self.assertPathPerm(False, 'user',      'module', '/multiple/1/user')
        self.assertPathPerm(True,  'someone',   'module', '/multiple/1/user')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/1/group')
        self.assertPathPerm(False, 'user',      'module', '/multiple/1/group')
        self.assertPathPerm(True,  'someone',   'module', '/multiple/1/group')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/1/auth')
        self.assertPathPerm(False, 'user',      'module', '/multiple/1/auth')
        self.assertPathPerm(False, 'someone',   'module', '/multiple/1/auth')
        self.assertPathPerm(False, 'anonymous', 'module', '/multiple/1/star')
        self.assertPathPerm(False, 'user',      'module', '/multiple/1/star')
        self.assertPathPerm(False, 'someone',   'module', '/multiple/1/star')

        self.assertPathPerm(False, 'anonymous', '',       '/multiple/2')
        self.assertPathPerm(False, 'user',      '',       '/multiple/2')
        self.assertPathPerm(False, 'someone',   '',       '/multiple/2')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/2')
        self.assertPathPerm(True,  'user',      'module', '/multiple/2')
        self.assertPathPerm(True,  'someone',   'module', '/multiple/2')
        self.assertPathPerm(False, 'anonymous', 'module', '/multiple/2/user')
        self.assertPathPerm(True,  'user',      'module', '/multiple/2/user')
        self.assertPathPerm(False, 'someone',   'module', '/multiple/2/user')
        self.assertPathPerm(False, 'anonymous', 'module', '/multiple/2/group')
        self.assertPathPerm(True,  'user',      'module', '/multiple/2/group')
        self.assertPathPerm(False, 'someone',   'module', '/multiple/2/group')
        self.assertPathPerm(False, 'anonymous', 'module', '/multiple/2/auth')
        self.assertPathPerm(True,  'user',      'module', '/multiple/2/auth')
        self.assertPathPerm(True,  'someone',   'module', '/multiple/2/auth')
        self.assertPathPerm(True,  'anonymous', 'module', '/multiple/2/star')
        self.assertPathPerm(True,  'user',      'module', '/multiple/2/star')
        self.assertPathPerm(True,  'someone',   'module', '/multiple/2/star')

    def test_changesets(self):
        # Changesets are allowed if at least one changed path is allowed, or
        # if the changeset is empty
        self.assertRevPerm(True, 'joe', 'scoped', 123)
        self.assertRevPerm(None, 'joe', 'scoped', 456)
        self.assertRevPerm(True, 'joe', 'scoped', 789)
        self.assertRevPerm(None, 'Jane', 'scoped', 123)
        self.assertRevPerm(True, 'Jane', 'scoped', 456)
        self.assertRevPerm(True, 'Jane', 'scoped', 789)
        self.assertRevPerm(None, 'user', 'scoped', 123)
        self.assertRevPerm(None, 'user', 'scoped', 456)
        self.assertRevPerm(True, 'user', 'scoped', 789)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuthzParserTestCase))
    suite.addTest(unittest.makeSuite(AuthzSourcePolicyTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
