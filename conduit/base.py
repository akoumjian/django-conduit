from importlib import import_module
from conduit.exceptions import HttpInterrupt

class Conduit(object):
    """
    Runs a request through a conduit and returns a response
    """
    def _get_method(self, method_string):
        method = getattr(self.__class__, method_string, None)
        if not method:
            pieces = method_string.split('.')
            if len(pieces) < 2:
                raise Exception('No such method found: {0}'.format(method_string))
            module = '.'.join(pieces[:-2])
            (cls, method,) = (pieces[-2], pieces[-1])
            module = import_module(module)
            cls = getattr(module, cls)
            method = getattr(cls, method)
        return method

    @classmethod
    def as_view(cls):
        """
        Returns a function for processing request response cycle
        """

        def view(request, *args, **kwargs):
            """
            Process the request, return a response
            """
            self = cls()
            for method_string in self.Meta.conduit[:-1]:
                method = self._get_method(method_string)
                try:
                    (request, args, kwargs,) = method(self, request, *args, **kwargs)
                except HttpInterrupt as e:
                    return e.response

            response_method = self._get_method(self.Meta.conduit[-1])
            return response_method(self, request, *args, **kwargs)

        return view