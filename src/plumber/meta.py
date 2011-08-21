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
            dct = x.__dict__
            fntocurry = "__call__"

        # ignored attributes in the plumber's __dict__
        blacklist = ['__doc__', '__module__']
        instructions = filter(
            lambda x: x[0] not in blacklist,
            plumber.__dict__.iteritems()
            )
        for name, instr in instructions:
            # here instructions need to be processed - for now we collide
            if name in dct:
                raise Exception("Collision: %s" % (k,))

            # in case of instances functions need to be bound
            if not x_is_class and (type(instr) is types.FunctionType):
                instr = instr.__get__(x)

            dct[name] = instr

        # check whether to curry something
        if (cargs or defkw) and fntocurry in dct:
            dct[fntocurry] = curry(dct[fntocurry], cargs, defkw)

        if x_is_class:
            name = "%s_%s" % (plumber.__name__, x.__name__)
            x = type(x)(name, x.__bases__, dct)
        return x

    def __add__(plumber, other):
        """plumber1 + plumber2 is equivalent to plumber1(plumber2)

        XXX: not sure whether this is a good idea
        """
        return plumber(other)

    def __iter__(plumber):
        """iterate over the keys of a plumber's __dict__
        """
        return iter(plumber.__dict__)
