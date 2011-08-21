from plumber import Plumber


def compose(*args, **kw):
    x = args[0]
    xs = args[1:]
    if not xs:
        return curry(x, **kw) if kw else x
    if not issubclass(x, Plumber):
        raise Exception("All except last need to be plumbers.")
    return x(compose(*xs), **kw)
