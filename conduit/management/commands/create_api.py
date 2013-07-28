import os
from django.core.management.base import BaseCommand
from optparse import make_option
from conduit.api.utils import AutoAPI


class Command(BaseCommand):
    """
    Create API Boilerplate from one or more django apps

    ./manage.py create_api my_app my_other_app
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '--folder',
            action='store',
            default=None,
            dest='folder'
        ),
    )

    def handle(self, *args, **options):
        api = AutoAPI(*args)
        folder = options.get('folder', None)
        if folder:
            wd = os.getcwd()
            api_folder = os.path.join(wd, 'api')
            api_init = os.path.join(api_folder, '__init__.py')
            api_urls = os.path.join(api_folder, 'urls.py')
            api_views = os.path.join(api_folder, 'views.py')

            os.mkdir(api_folder)

            # Create empty init file
            with open(api_init, 'a') as f:
                pass

            with open(api_urls, 'w') as f:
                f.write(api.__urlconf_str__())

            with open(api_views, 'w') as f:
                f.write(api.__resource_str__())
            return 'Created API files in {0}'.format(api_folder)
        else:
            return api.__to_string__()
