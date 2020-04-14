
class Context(object):
    sid = None
    is_preop = None
    splunk_server = None
    root_trace_context_string = None


class Result(object):

    data = None
    final = None
    wait = None

    def __init__(
        self,
        data=None,
        final=True,
        wait=False,
    ):
        self.data = data
        self.final = final
        self.wait = wait


__all__ = [
    "Context",
    "Result",
]
