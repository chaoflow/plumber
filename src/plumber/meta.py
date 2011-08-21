from plumber._instructions import Instruction
from plumber._instructions import finalize
from plumber.exceptions import PlumbingCollision
from plumber.tools import Bases


class Instructions(object):
    """Adapter to store instructions on a plumber

    >>> class P(object): pass
    >>> instrs = Instructions(P)
    >>> instrs.append(1)
    >>> instrs.instructions
    [1]
    >>> instrs = Instructions(P)
    >>> instrs.instructions
    [1]
    """
    attrname = "__plumbing_instructions__"

    @property
    def instructions(self):
        return getattr(self.plumber, self.attrname)

    def __getattr__(self, name):
        return getattr(self.instructions, name)

    # XXX: needed explicitly to make it iterable?
    def __iter__(self):
        return self.instructions.__iter__()

    def __init__(self, plumber):
        self.plumber = plumber
        if not plumber.__dict__.has_key(self.attrname):
            setattr(plumber, self.attrname, [])

    def __repr__(self):
        return repr(
            [(x.name, x.__class__, x.payload) for x in self.instructions]
            )


class PlumberMeta(type):
    """meta class for plumbers
    """
    def __call__(plumber, x, *cargs, **defkw):
        """Do a plumbers work

        ``plumber``: a plumber class
        ``x``: a class/instance to work on
        ``cargs``: args to use for currying of __init__/__call__
        ``defkw``: default kws for __init__/__call__

        If x is a class:
        Create a new class with the same bases and apply the plumber to it.

        If x is an instance:
        Apply plumber to it - XXX! adapt
        """
        # instances of normal classes are modified in place
        # for classes, new classes are created
        x_is_class = issubclass(type(x), type)
        if x_is_class:
            dct = x.__dict__.copy()
            fntocurry = "__init__"
        else:
            raise 
            dct = x.__dict__
            fntocurry = "__call__"

        bases = Bases(x)
        for instr in Instructions(plumber):
            try:
                instr(dct, bases)
            except PlumbingCollision:
                raise PlumbingCollision(instr.name, plumber, x)

            # in case of instances functions need to be bound
            # if not x_is_class and (type(instr) is types.FunctionType):
            #     instr = instr.__get__(x)

        # check whether to curry something
        if (cargs or defkw) and fntocurry in dct:
            dct[fntocurry] = curry(dct[fntocurry], cargs, defkw)

        if x_is_class:
            name = "%s_%s" % (plumber.__name__, x.__name__)
            x = type(x)(name, x.__bases__, dct)
        return x

    def __init__(plumber, name, bases, dct):
        """Will be called when a plumber class is created

        Parse the plumbers dictionary and generate instructions from it.
        Undecorated attributes are understood as finalize instructions.

        >>> from plumber import Plumber
        >>> from plumber import Instruction
        >>> class P(Plumber):
        ...     a = Instruction(1)
        ...     b = 2
        >>> Instructions(P)
        [('a', <class 'plumber._instructions.Instruction'>, 1),
         ('b', <class 'plumber._instructions.finalize'>, 2)]
        """
        super(PlumberMeta, plumber).__init__(name, bases, dct)

        # Get the plumber's instructions list
        instructions = Instructions(plumber)

        for name, item in plumber.__dict__.iteritems():
            # ignored attributes
            if name.startswith('__plumb'): continue
            if name in ['__doc__', '__module__']: continue

            # undecorated items are understood as finalize
            if not isinstance(item, Instruction):
                item = finalize(item)
            item.__name__ = name
            item.__parent__ = plumber
            instructions.append(item)


        # # An existing docstring is an implicit plumb instruction for __doc__
        # if plumber.__doc__ is not None:
        #     instructions.append(plumb(plumber.__doc__, name='__doc__'))

        # # If zope.interface is available treat existence of implemented
        # # interfaces as an implicit _implements instruction with these
        # # interfaces.
        # if ZOPE_INTERFACE_AVAILABLE:
        #     instructions.append(_implements(plumber))

        # # XXX: introduce C3 resolution
        # # check our bases for instructions we don't have already and which
        # # are not overwritten by our instructions (stage1)
        # for base in bases:
        #     # XXX: I don't like this code
        #     for instr in Instructions(base):
        #         # skip instructions we have already
        #         if instr in instructions:
        #             continue
        #         # stage1 instructions with the same name are ignored
        #         if instr.__name__ in [x.__name__ for x in instructions if
        #                 x.__stage__ == 'stage1']:
        #             continue
        #         instructions.append(instr)

    # def __add__(plumber, other):
    #     """plumber1 + plumber2 is equivalent to plumber1(plumber2)

    #     XXX: not sure whether this is a good idea
    #     """
    #     return plumber(other)

    # def __iter__(plumber):
    #     """iterate over the keys of a plumber's __dict__
    #     """
    #     return iter(plumber.__dict__)
