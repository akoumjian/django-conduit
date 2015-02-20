try:
    from django.test.runner import DiscoverRunner as BaseRunner
except ImportError:
    # Django < 1.6 fallback
    from django.test.simple import DjangoTestSuiteRunner as BaseRunner
from django.conf import settings
from django.utils.unittest import TestSuite
from django.test.runner import dependency_ordered
 
class NonGeoTestRunner( BaseRunner ):
    """
    The default test runner for Django 
    will attempt to create all databases in settings.DATABASES.
    For local development and quick "spot-checks" with the unit tests
    the installation, dependencies, permissions, and time required to set up Postgresql/PostGIS might be annoying.
    We can use this test runner to avoid setting up the PostGIS database and running related tests:
    `python example/manage.py test --testrunner='conduit.test.non_geo_testrunner.NonGeoTestRunner'`
    """

    def build_suite(self, *args, **kwargs):
        suite = super(NonGeoTestRunner, self).build_suite(*args, **kwargs)
        filtered_suite = TestSuite()
        filtered_suite.addTests( [ test for test in suite if test.__class__.__name__ != 'GeoMethodTestCase' ] )
        return filtered_suite
 
    def setup_databases(self, **kwargs):
        return setup_databases(self.verbosity, self.interactive, **kwargs)


def setup_databases(verbosity, interactive, **kwargs):
    """
    modified version of the same function located in 
    site-packages/django/test/runner.py.
    this version will not add a database connection
    to 'test_databases' for creation if it finds
    the ENGINE setting for postgis
    """
    from django.db import connections, DEFAULT_DB_ALIAS

    # First pass -- work out which databases actually need to be created,
    # and which ones are test mirrors or duplicate entries in DATABASES
    mirrored_aliases = {}
    test_databases = {}
    dependencies = {}
    default_sig = connections[DEFAULT_DB_ALIAS].creation.test_db_signature()
    for alias in connections:
        connection = connections[alias]
        #
        #  DIFF
        #
        if connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis':
            continue
        #
        #  END DIFF
        #
        if connection.settings_dict['TEST_MIRROR']:
            # If the database is marked as a test mirror, save
            # the alias.
            mirrored_aliases[alias] = (
                connection.settings_dict['TEST_MIRROR'])
        else:
            # Store a tuple with DB parameters that uniquely identify it.
            # If we have two aliases with the same values for that tuple,
            # we only need to create the test database once.
            item = test_databases.setdefault(
                connection.creation.test_db_signature(),
                (connection.settings_dict['NAME'], set())
            )
            item[1].add(alias)

            if 'TEST_DEPENDENCIES' in connection.settings_dict:
                dependencies[alias] = (
                    connection.settings_dict['TEST_DEPENDENCIES'])
            else:
                if alias != DEFAULT_DB_ALIAS and connection.creation.test_db_signature() != default_sig:
                    dependencies[alias] = connection.settings_dict.get(
                        'TEST_DEPENDENCIES', [DEFAULT_DB_ALIAS])

    # Second pass -- actually create the databases.
    old_names = []
    mirrors = []

    for signature, (db_name, aliases) in dependency_ordered(
        test_databases.items(), dependencies):
        test_db_name = None
        # Actually create the database for the first connection
        for alias in aliases:
            connection = connections[alias]
            if test_db_name is None:
                test_db_name = connection.creation.create_test_db(
                        verbosity, autoclobber=not interactive)
                destroy = True
            else:
                connection.settings_dict['NAME'] = test_db_name
                destroy = False
            old_names.append((connection, db_name, destroy))

    for alias, mirror_alias in mirrored_aliases.items():
        mirrors.append((alias, connections[alias].settings_dict['NAME']))
        connections[alias].settings_dict['NAME'] = (
            connections[mirror_alias].settings_dict['NAME'])

    return old_names, mirrors
