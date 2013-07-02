class HttpInterrupt(Exception):
    """
    Raise when req/resp cycle should end early and serve response

    ie: If an authorization fails, we can stop the conduit
    and serve an error message
    """
    def __init__(self, response):
        self.response = response or HttpResponse('No content')