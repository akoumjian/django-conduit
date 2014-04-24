## Tests are located where Django 1.6 expects them. We import them
## here to be backwards compatible.
## https://docs.djangoproject.com/en/dev/releases/1.6/#backwards-incompatible-changes-in-1-6
from conduit.test.test_modelresource_methods import *
from conduit.test.test_custom_pkfield_overrides import *
from conduit.test.test_modelresource_conduit_formats import *
