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

def plumb_str(leftdoc, rightdoc):
    """helper function to plumb two doc strings together

    A ``__plbnext__`` tag is replaced with rightdoc, it needs to be preceeded
    and followed by an empty line::

        >>> leftdoc = '''Left head
        ...
        ... __plbnext__
        ...
        ... Left tail
        ... '''

        >>> rightdoc = '''Right head
        ...
        ... __plbnext__
        ...
        ... Right tail
        ... '''

        >>> print plumb_str(leftdoc, rightdoc)
        Left head
        <BLANKLINE>
        Right head
        <BLANKLINE>
        __plbnext__
        <BLANKLINE>
        Right tail
        <BLANKLINE>
        Left tail
        <BLANKLINE>

    Otherwise leftdoc is appended to rightdoc, separated by a newline, it is
    assumed there is a ``__plbnext__`` tag at the beginning of leftdoc::

        >>> leftdoc = '''Left tail
        ... '''
        >>> rightdoc = '''Right tail
        ... '''
        >>> print plumb_str(leftdoc, rightdoc)
        Right tail
        <BLANKLINE>
        Left tail
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
    _next = re.search("\n\s*\n\s*__plbnext__\s*\n\s*\n", leftdoc)
    if not _next:
        return "\n\n".join((rightdoc.rstrip(), leftdoc))
    return leftdoc.replace('__plbnext__', rightdoc.rstrip())


class Instruction(object):
    """Base class for all plumbing instructions

    An instruction works on the attribute sharing its name, parent is the part
    declaring it. An instruction declares the stage to be applied in.
    """
    __stage__ = None

    def __repr__(self):
        return "<%(cls)s '%(name)s' of %(parent)s payload=%(payload)s>" % dict(
                cls=self.__class__.__name__,
                name=self.name or 'None',
                parent=self.__parent__ or 'None',
                payload=repr(self.payload))

    __str__ = __repr__


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
        """
            >>> plb1 = plumb(1)
            >>> plb1 + plumb(1) is plb1
            True

            >>> plb1 + Instruction(1)
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <plumb 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload=1>

            >>> plumb(lambda x: None) + plumb(property(lambda x: None))
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <plumb 'None' of None payload=<function <lambda> at 0x...>>
              with:
                <plumb 'None' of None payload=<property object at 0x...>>
        """
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

            >>> plumb(1) + plumb(2)
            Traceback (most recent call last):
              ...
            PlumbingCollision:
                <plumb 'None' of None payload=1>
              with:
                <plumb 'None' of None payload=2>

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
                if p2func is None:
                    propfuncs.append(p1func)
                elif type(p2func) is extend:
                    propfuncs.append(p2func.payload)
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
