Plumber base class::

    >>> from plumber import Plumber

Two plumbers used on class Plumbing::

    >>> class f(Plumber):
    ...     a = 1
    >>> class g(Plumber):
    ...     b = 2

    >>> class Base(object):
    ...     b = 3

    >>> @f
    ... @g
    ... class Plumbing(Base):
    ...     c = 3

    >>> Plumbing.a
    1
    >>> Plumbing.b
    2
    >>> Plumbing.c
    3

    >>> p = Plumbing()
    >>> p.a
    1
    >>> p.b
    2
    >>> p.c
    3

.. different syntax::

..     >>> @f(g)
..     ... class Plumbing(object):
..     ...     c = 3

..     >>> Plumbing.a
..     1
..     >>> Plumbing.b
..     2
..     >>> Plumbing.c
..     3

..     >>> p = Plumbing()
..     >>> p.a
..     1
..     >>> p.b
..     2
..     >>> p.c
..     3

.. different syntax::

..     >>> from plumber import compose

..     >>> @compose(f, g)
..     ... class Plumbing(object):
..     ...     c = 3

..     >>> Plumbing.a
..     1
..     >>> Plumbing.b
..     2
..     >>> Plumbing.c
..     3

..     >>> p = Plumbing()
..     >>> p.a
..     1
..     >>> p.b
..     2
..     >>> p.c
..     3

Collision::

    >>> class f(Plumber):
    ...     a = 1

    >>> @f
    ... class Plumbing(object):
    ...     a = 2
    Traceback (most recent call last):
      ...
    PlumbingCollision: 'a'
        <class 'f'>
      collides with:
        <class 'Plumbing'>

default instruction::

    >>> from plumber import default
    >>> class f(Plumber):
    ...     a = default(1)
    ...     b = default(1)
    ...     c = default(1)

    >>> class Base(object):
    ...     b = 2

    >>> @f
    ... class Plumbing(Base):
    ...     c = 3

    >>> Plumbing.a
    1
    >>> Plumbing.b
    2
    >>> Plumbing.c
    3

overwrite instruction::

    >>> from plumber import overwrite
    >>> class f(Plumber):
    ...     a = overwrite(1)
    ...     b = overwrite(1)
    ...     c = overwrite(1)

    >>> class g(Plumber):
    ...     c = overwrite(2)

    >>> class Base(object):
    ...     b = 3

    >>> @f
    ... @g
    ... class Plumbing(Base):
    ...     a = 4

    >>> Plumbing.a
    4
    >>> Plumbing.b
    1
    >>> Plumbing.c
    1

finalize instruction::

    >>> from plumber import finalize
    >>> class f(Plumber):
    ...     a = finalize(1)

    >>> class g(Plumber):
    ...     a = overwrite(2)

    >>> @f
    ... @g
    ... class Plumbing(object):
    ...     pass

    >>> Plumbing.a
    1

plumb instruction::

    .. >>> from plumber import plumb
    .. >>> class f(Plumber):
    .. ...     @plumb
    .. ...     def func(_next, self):
    .. ...         return 2 * _next()

    .. >>> @f
    .. ... class Plumbing(object):
    .. ...     def func(self):
    .. ...         return 3

    .. >>> p = Plumbing()
    .. >>> p.func()
    .. 6

