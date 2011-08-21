from plumber.exceptions import PlumbingCollision


def payload(item):
    """Get to the payload through a chain of instructions

        >>> class Foo: pass
        >>> payload(Instruction(Instruction(Foo))) is Foo
        True
    """
    if not isinstance(item, Instruction):
        return item
    return payload(item.item)


class Instruction(object):
    __name__ = None
    __parent__ = None

    @property
    def name(self):
        """Name of the attribute the instruction is for
        """
        return self.__name__

    @property
    def payload(self):
        return payload(self)

    def check(self, dct, bases, stack):
        """Check whether to apply an instruction::

        ``bases`` is a wrapper for all base classes of the plumbing and
        provides ``__contains__``, instructions may or may not need it.
        """
        raise NotImplementedError #pragma NO COVERAGE

    def __call__(self, dct, bases):
        stack = dct.setdefault('__plumbing_stacks__', {}).setdefault(self.name, [])
        if stack and (stack[-1] == self) or not self.check(dct, bases, stack):
            return
        dct[self.name] = self.payload
        stack.append(self)

    def __eq__(self, right):
        """Instructions are equal if ...

        - they are the very same
        - their class is the very same and their payloads are equal
        """
        if self is right:
            return True
        if not self.__class__ is right.__class__:
            return False
        if self.name == right.name and payload == right.payload:
            return True
        return False

    def __init__(self, item, name=None):
        """
            >>> class Foo: pass
            >>> Instruction(Foo).item is Foo
            True
            >>> Instruction(Foo).__name__ is None
            True
            >>> Instruction(Foo, name='foo').__name__ == 'foo'
            True

            The name can be provided here for easier testing
        """
        self.item = item
        if name is not None:
            self.__name__ = name


class default(Instruction):
    """
        >>> dct = dict(a=1)
        >>> bases = dict(b=2)

        >>> d1 = default(3, "a")
        >>> d1(dct, bases)
        >>> dct.get('a')
        1

        >>> d2 = default(3, "b")
        >>> d2(dct, bases)
        >>> dct.get('b', "no")
        'no'

        >>> d3 = default(3, "c")
        >>> d3(dct, bases)
        >>> dct.get('c')
        3
    """
    priority = 0

    def check(self, dct, bases, prev):
        return (self.name not in dct and self.name not in bases)


class finalize(Instruction):
    """
        >>> dct = dict(a=1)
        >>> bases = dict(b=2)
        >>> f1 = finalize(3, "a")
        >>> f1(dct, bases)
        Traceback (most recent call last):
        ...
        PlumbingCollision: a

        >>> f2 = finalize(3, "b")
        >>> f2(dct, bases)
        >>> f2(dct, bases)
        >>> dct['b']
        3
    """
    priority = 20

    def check(self, dct, bases, stack):
        if self.name not in dct: return True
        if not stack or self.__class__ is stack[-1].__class__:
            raise PlumbingCollision(self.name)
        return True


class overwrite(Instruction):
    priority = 10

    def check(self, dct, bases, stack):
        if self.name not in dct: return True
        if not stack: return False
        return stack[-1].priority <= self.priority
