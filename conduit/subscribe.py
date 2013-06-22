from functools import wraps


def subscribe(sub=None):
    """
    Runs the wrapped method if sub matches any pub namespaces

    ie: "if any"
    """
    def func_wrapper(func):
        @wraps(func)
        def returned_wrapper(self, request, *args, **kwargs):
            for name in sub:
                if name in kwargs['pub']:
                    return func(self, request, *args, **kwargs)
            return request, args, kwargs
        return returned_wrapper
    return func_wrapper


def avoid(avoid=None):
    """
    Avoids running the method if any avoid string matches a pub

    ie: "if none of these"
    """
    def func_wrapper(func):
        @wraps(func)
        def returned_wrapper(self, request, *args, **kwargs):
            for name in avoid:
                if name in kwargs['pub']:
                    return request, args, kwargs
            return func(self, request, *args, **kwargs)
        return returned_wrapper
    return func_wrapper


def match(match=None):
    """
    Runs the wrapped method if we match all the sub words

    ie: "if and only if all of these"
    """
    def func_wrapper(func):
        @wraps(func)
        def returned_wrapper(self, request, *args, **kwargs):
            for name in match:
                if name not in kwargs['pub']:
                    return request, args, kwargs
            return func(self, request, *args, **kwargs)
        return returned_wrapper
    return func_wrapper