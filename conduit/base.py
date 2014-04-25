from importlib import import_module
from conduit.exceptions import HttpInterrupt
from django.db import transaction

class Conduit(object):
    """
    Runs a request through a conduit and returns a response
    """
    def _get_method(self, method_string):
        method = getattr(self.__class__, method_string, None)
        cls = self.__class__
        if not method:
            pieces = method_string.split('.')
            if len(pieces) < 2:
                raise Exception('No such method found: {0}'.format(method_string))
            module = '.'.join(pieces[:-2])
            (cls, method,) = (pieces[-2], pieces[-1])
            module = import_module(module)
            cls = getattr(module, cls)
            method = getattr(cls, method)
        bound_method = method.__get__( self, cls )
        return bound_method

    def view(self, request, *args, **kwargs):
        """
        Process the request, return a response
        """
        # self = cls()
        try:
            # Wrap the request in a transaction
            # If we see an exception (such as HttpInterrupt)
            # all model changes will be rolled back
            with transaction.commit_on_success():
                for method_string in self.Meta.conduit[:-1]:
                    bound_method = self._get_method(method_string)
                    (request, args, kwargs,) = bound_method( request, *args, **kwargs)
        except HttpInterrupt as e:
            return e.response

        bound_response_method = self._get_method(self.Meta.conduit[-1])
        return bound_response_method(request, *args, **kwargs)
