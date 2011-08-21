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

    def apply(self, dct, base, stack):
        """apply the instruction

        May raise exceptions:
        - PlumbingCollision

        return True (applied) / False (not applied)
        """
        raise NotImplementedError #pragma NO COVERAGE

    def __call__(self, dct, bases):
        stack = dct.setdefault('__plumbing_stacks__', {}).setdefault(self.name, [])
        if self.apply(dct, bases, stack):
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
        if self.name != right.name:
            return False
        if self.payload != right.payload:
            return False
        return True

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


class EitherOrInstruction(Instruction):
    """Instructions where either an existing value or the provided one is used
    """
    def apply(self, dct, bases, stack):
        if stack and (stack[-1] == self):
            return False
        if self.check(dct, bases, stack):
            dct[self.name] = self.payload
        return True

    def check(self, dct, bases, stack):
        """Check whether to apply an instruction

        ``bases`` is a wrapper for all base classes of the plumbing and
        provides ``__contains__``, instructions may or may not need it.
        """
        raise NotImplementedError #pragma NO COVERAGE


class default(EitherOrInstruction):
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
    def check(self, dct, bases, prev):
        return (self.name not in dct and self.name not in bases)


class finalize(EitherOrInstruction):
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
    def check(self, dct, bases, stack):
        if self.name not in dct: return True
        if not stack or isinstance(stack[-1], finalize):
            raise PlumbingCollision(self.name)
        return True


class overwrite(EitherOrInstruction):
    def check(self, dct, bases, stack):
        if self.name not in dct:
            return True
        if not stack:
            return False
        if isinstance(stack[-1], finalize):
            return False
        return True
