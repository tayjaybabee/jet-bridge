
class Response(object):
    headers = {'Content-Type': 'text/html'}

    def __init__(self, data=None, status=None, headers=None, exception=False, content_type=None):
        self.data = data
        self.status = status
        self.exception = exception
        self.content_type = content_type

        if headers:
            self.headers.update(headers)

    def header_items(self):
        return self.headers.items() if self.headers else []

    def render(self):
        return bytes() if self.data is None else self.data
