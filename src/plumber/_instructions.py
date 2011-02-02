"""Instructions to be used in a plumbing part's declaration
"""
import re
import types

try:
    from zope.interface import classImplements
    from zope.interface import implementedBy
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError: #pragma NO COVERAGE
    ZOPE_INTERFACE_AVAILABLE = False #pragma NO COVERAGE

from plumber.exceptions import PlumbingCollision


####
# Instruction base class and helper function
#

def payload(item):
    """Get to the payload through a chain of instructions

        >>> class Foo: pass
        >>> payload(Instruction(Instruction(Foo))) is Foo
        True
    """
    if not isinstance(item, Instruction):
        return item
    return payload(item.item)


def plumb_str(leftdoc, rightdoc):
    """helper function to plumb two doc strings together

    A ``.. plbnext::`` tag is replaced with rightdoc::

        >>> leftdoc = '''Left head
        ... .. plbnext::
        ... Left tail
        ... '''

        >>> rightdoc = '''Right head
        ... .. plbnext::
        ... Right tail
        ... '''

        >>> print plumb_str(leftdoc, rightdoc)
        Left head
        Right head
        .. plbnext::
        Right tail
        <BLANKLINE>
        Left tail
        <BLANKLINE>

    Otherwise rightdoc is just appended to leftdoc, separated by a newline::

        >>> leftdoc = '''Left doc
        ... '''
        >>> rightdoc = '''Right doc
        ... '''
        >>> print plumb_str(leftdoc, rightdoc)
        Left doc
        <BLANKLINE>
        Right doc
        <BLANKLINE>

        >>> class A: pass
        >>> plumb_str(A, None) is A
        True
        >>> plumb_str(None, A) is A
        True
        >>> plumb_str(None, None) is None
        True
    """
    if leftdoc is None:
        return rightdoc
    if rightdoc is None:
        return leftdoc
    _next = re.search("\n".join(('', "\s*.. plbnext::\s*", '')), leftdoc)
    if not _next:
        return "\n".join((leftdoc, rightdoc))
    return "\n".join((
            leftdoc[:_next.start()],
            rightdoc,
            leftdoc[_next.end():]
            ))


class Instruction(object):
    """Base class for all plumbing instructions

    An instruction works on the attribute sharing its name, parent is the part
    declaring it. An instruction declares the stage to be applied in.
    """
    __name__ = None
    __parent__ = None
    __stage__ = None

    def __init__(self, item, name=None):
        """
            >>> class Foo: pass
            >>> Instruction(Foo).item is Foo
            True
            >>> Instruction(Foo).__name__ is None
            True
            >>> Instruction(Foo, name='foo').__name__ == 'foo'
            True
        """
        self.item = item
        if name is not None:
            self.__name__ = name

    def __add__(self, right):
        """Used to merge instructions, subclasses need to implement it::

            >>> Instruction(None) + 1
            Traceback (most recent call last):
              ...
            NotImplementedError
        """
        raise NotImplementedError

    def __call__(self, dct, bases=None):
        """Apply instruction to a plumbing, subclasses need to implement it::

            >>> Instruction(None)(None)
            Traceback (most recent call last):
              ...
            NotImplementedError

        ``bases`` is a wrapper for all base classes of the plumbing and
        provides ``__contains__``, instructions may or may not need it.
        """
        raise NotImplementedError

    def __eq__(self, right):
        """Instructions are equal if ...

        - they are the very same
        - their class is the very same and their payloads are equal
        """
        # breaking up boolean expressions makes them more transparent for test
        # coverage
        if self is right:
            return True
        if not self.__class__ is right.__class__:
            return False
        if self.name == right.name:
            if self.payload == right.payload:
                return True
        return False

    @property
    def name(self):
        return self.__name__

    @property
    def payload(self):
        return payload(self)

    def __repr__(self):
        return "<%(cls)s '%(name)s' of %(parent)s payload=%(payload)s>" % dict(
                cls=self.__class__.__name__,
                name=self.name or 'None',
                parent=self.__parent__ or 'None',
                payload=repr(self.payload))

    __str__ = __repr__


####
# Stage 1 instructions
#

class Stage1Instruction(Instruction):
    """Instructions installed in stage1

    - default
    - extend
    - finalize
    """
    __stage__ = 'stage1'


class default(Stage1Instruction):
    """Provide a default attribute

    A default attribute is used, if neither the class nor one of its bases
    declare the attribute.

    For default/extend/finalize merging see ``__add__`` here,
    ``extend.__add__`` and ``finalize.__add__``.
    """
    def __add__(self, right):
        """
        First default wins from left to right::

            >>> def1 = default(1)
            >>> def1 + def1 is def1
            True
            >>> def2 = default(2)
            >>> def1 + def2 is def1
            True
            >>> def2 + def1 is def2
            True

        Extend wins over default::

            >>> ext3 = extend(3)
            >>> def1 + ext3 is ext3
            True

        Finalize wins over default::

            >>> fin4 = finalize(4)
            >>> def1 + fin4 is fin4
            True

        Adding with something else than default/extend, raises
        ``PlumbingCollision``::

            >>> def1 + Instruction('foo')
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <default 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload='foo'>
        """
        if self == right:
            return self
        if isinstance(right, default):
            return self
        if isinstance(right, extend):
            return right
        if isinstance(right, finalize):
            return right
        raise PlumbingCollision(self, right)

    def __call__(self, dct, bases):
        if not dct.has_key(self.name) and not self.name in bases:
            dct[self.name] = self.payload


class extend(Stage1Instruction):
    """Extend the class with an attribute

    An ``extend`` attribute overrides an attribute defined on a base class or
    provided by ``default``, but is overridden by ``finalize`` and attributes
    declared on the plumbing class (implicit ``finalize``).

    The first ``extend`` will be picked over later ``extend``.

    For default/extend/finalize merging see ``__add__`` here,
    ``default.__add__`` and ``finalize.__add__``.
    """
    def __add__(self, right):
        """
        First extend wins against following equal extends and arbitrary
        defaults::

            >>> ext1 = extend(1)
            >>> ext1 + ext1 is ext1
            True
            >>> ext1 + extend(1) is ext1
            True
            >>> ext1 + extend(2) is ext1
            True
            >>> ext1 + default(2) is ext1
            True
            >>> fin3 = finalize(3)
            >>> ext1 + fin3 is fin3
            True

        Everything except default/extend collides::

            >>> ext1 + Instruction(1)
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <extend 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload=1>
        """
        if self == right:
            return self
        if isinstance(right, default):
            return self
        if isinstance(right, extend):
            return self
        if isinstance(right, finalize):
            return right
        raise PlumbingCollision(self, right)

    def __call__(self, dct, bases):
        if dct.has_key(self.name):
            return
        dct[self.name] = self.payload


class finalize(Stage1Instruction):
    """Insist on the final value / finalize the endpoint

    A ``finalize`` attribute is chosen over all others, two ``finalize``
    collide, declarations on the plumbing class are implicit ``finalize``
    declarations.

    For default/extend/finalize merging see ``__add__`` here,
    ``default.__add__`` and ``extend.__add__``.
    """
    def __add__(self, right):
        """
        First extend wins against following equal extends and arbitrary
        defaults::

            >>> fin1 = finalize(1)
            >>> fin1 + fin1 is fin1
            True
            >>> fin1 + finalize(1) is fin1
            True
            >>> fin1 + default(2) is fin1
            True
            >>> fin1 + extend(2) is fin1
            True

        Two unequal finalize collide::

            >>> fin1 + finalize(2)
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <finalize 'None' of None payload=1>
              with:
                <finalize 'None' of None payload=2>

        Everything except default/extend collides::

            >>> fin1 + Instruction(1)
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <finalize 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload=1>
        """
        if self == right:
            return self
        if isinstance(right, default):
            return self
        if isinstance(right, extend):
            return self
        raise PlumbingCollision(self, right)

    def __call__(self, dct, bases):
        if dct.has_key(self.name):
            raise PlumbingCollision('Plumbing class', self)
        dct[self.name] = self.payload


####
# Stage2 instructions
#

class Stage2Instruction(Instruction):
    """Instructions installed in stage2: so far only plumb
    """
    __stage__ = 'stage2'

    def __call__(self, cls):
        """cls is the plumbing class, type finished its work already
        """
        raise NotImplementedError #pragma NO COVERAGE


def entrancefor(plumbing_method, _next):
    """An entrance for a plumbing method, given _next

    The entrance returned is a closure with signature: (self, *args, **kw), it
    wraps a call of plumbing_method curried with _next.
    """
    def entrance(self, *args, **kw):
        return plumbing_method(_next, self, *args, **kw)
    entrance.__doc__ = plumb_str(plumbing_method.__doc__, _next.__doc__)
    entrance.__name__ = plumbing_method.__name__
    return entrance


def plumbingfor(plumbing_method, _next):
    """A plumbing method combining two plumbing methods
    """
    def plumbing(__next, self, *args, **kw):
        return plumbing_method(
                    entrancefor(_next, __next),
                    self, *args, **kw
                    )
    plumbing.__doc__ = plumb_str(plumbing_method.__doc__, _next.__doc__)
    plumbing.__name__ = plumbing_method.__name__
    return plumbing


class plumb(Stage2Instruction):
    """Plumbing of strings, methods and properties

    XXX: support getter, setter, deleter to enable:

    @plumb
    @property
    def foo

    @foo.setter
    def foo
    """
    def __add__(self, right):
        if self == right:
            return self
        if not isinstance(right, plumb):
            raise PlumbingCollision(self, right)
        if not self.ok(self.payload, right.payload):
            raise PlumbingCollision(self, right)
        return plumb(self.plumb(plumbingfor, self.payload, right.payload),
                     name=self.name)

    def ok(self, p1, p2):
        """Check whether we can merge two payloads
        """
        if isinstance(p1, basestring):
            return isinstance(p2, basestring) or p2 is None
        if isinstance(p1, property):
            return isinstance(p2, property)
        if callable(p1):
            return callable(p2)
        return False

    def plumb(self, plbfunc, p1, p2):
        if isinstance(p1, basestring):
            return plumb_str(p1, p2)
        if isinstance(p1, property):
            # XXX: This should be split up into instructions during part
            # parsing to enable two stages and all instructions
            propfuncs = []
            for x in 'fget', 'fset', 'fdel':
                p1func = getattr(p1, x)
                p2func = getattr(p2, x)
                if p1func is None:
                    propfuncs.append(p2func)
                elif type(p1func) is extend:
                    propfuncs.append(p1func.payload)
                else:
                    propfuncs.append(plbfunc(p1func, p2func))
            propfuncs.append(plumb_str(p1.__doc__, p2.__doc__))
            return p1.__class__(*propfuncs)
        if callable(p1):
            return plbfunc(p1, p2)
        raise RuntimeError("We should not reach this code!") #pragma NO COVERAGE

    def __call__(self, cls):
        # Check for a method on the plumbing class itself.
        _next = getattr(cls, self.name)
        if not self.ok(self.payload, _next):
            raise PlumbingCollision(self, cls)
        entrance = self.plumb(entrancefor, self.payload, _next)
        setattr(cls, self.name, entrance)


class plumbifexists(plumb):
    """Only plumb, if an end point exists
    """
    def __call__(self, cls):
        try:
            super(plumbifexists, self).__call__(cls)
        except AttributeError:
            pass


if ZOPE_INTERFACE_AVAILABLE:
    class _implements(Stage2Instruction):
        """classImplements interfaces

            >>> foo = _implements(('foo',))
            >>> foo == foo
            True
            >>> foo + foo is foo
            True

            >>> foo == _implements(('foo',))
            True
            >>> foo != _implements(('bar',))
            True

            >>> _implements(('foo', 'bar')) == _implements(('bar', 'foo'))
            True

            >>> foo + _implements(('foo',)) is foo
            True

            >>> bar = _implements(('bar',))
            >>> foo + bar
            <_implements '__interfaces__' of None payload=('bar', 'foo')>

            >>> foo + bar == bar + foo
            True

            >>> foo + Instruction("bar")
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <_implements '__interfaces__' of None payload=('foo',)>
              with:
                <Instruction 'None' of None payload='bar'>
        """
        __name__ = "__interfaces__"

        def __add__(self, right):
            if self == right:
                return self
            if not isinstance(right, _implements):
                raise PlumbingCollision(self, right)
            ifaces = self.payload + right.payload
            return _implements(ifaces)

        def __call__(self, cls):
            if self.payload:
                classImplements(cls, *self.payload)

        @property
        def payload(self):
            if type(self.item) is tuple:
                return tuple(sorted(self.item))
            return tuple(sorted(implementedBy(self.item)))
