Plumber base class::

    >>> from plumber import Plumber

Two plumbers used on class Plumbing::

    >>> class f(Plumber):
    ...     a = 1
    >>> class g(Plumber):
    ...     b = 2

    >>> @f
    ... @g
    ... class Plumbing(object):
    ...     c = 3

    >>> Plumbing.a
    1
    >>> Plumbing.b
    2
    >>> Plumbing.c
    3

Collision::

    >>> class f(Plumber):
    ...     a = 1

    >>> @f
    ... class Plumbing(object):
    ...     a = 2

