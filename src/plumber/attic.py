from plumber._part import Instructions
from plumber._part import partmetaclass


class Stacks(object):
    """organize stacks for parsing parts, stored in the class' dict
    """
    attrname = "__plumbing_stacks__"

    def __init__(self, dct):
        self.dct = dct
        self.dct.setdefault(self.attrname, dict())
        self.stacks.setdefault('stages', dict())
        self.stages.setdefault('stage1', dict())
        self.stages.setdefault('stage2', dict())
        self.stacks.setdefault('history', [])

    stacks = property(lambda self: self.dct[self.attrname])
    stages = property(lambda self: self.stacks['stages'])
    stage1 = property(lambda self: self.stages['stage1'])
    stage2 = property(lambda self: self.stages['stage2'])
    history = property(lambda self: self.stacks['history'])


class plumber(type):
    """Metaclass for plumbing creation

    Create and call a real plumber, for classes declaring a ``__plumbing__``
    attribute (inheritance is not enough):
    """
    def __new__(meta, name, bases, dct):
        if not dct.has_key('__plumbing__'):
            return type.__new__(meta, name, bases, dct)

        # turn single part into a tuple of one part
        if type(dct['__plumbing__']) is not tuple:
            dct['__plumbing__'] = (dct['__plumbing__'],)

        # stacks for parsing instructions
        stacks = Stacks(dct)

        # parse the parts
        for part in dct['__plumbing__']:
            for instruction in Instructions(part):
                stage = stacks.stages[instruction.__stage__]
                stack = stage.setdefault(instruction.__name__, [])
                stacks.history.append(instruction)
                if instruction not in stacks.history[:-1]:
                    if stack:
                        # XXX: replace by a non exception log warning
                        #if instruction.__stage__ > stack[-1].__stage__:
                        #    msg = 'Stage1 instruction %s left of stage2 '
                        #    'instruction %s. We consider deprecation of this.' \
                        #            % (stack[-1], instruction)
                        #    raise PendingDeprecationWarning(msg)
                        instruction = stack[-1] + instruction
                    stack.append(instruction)
                #else:
                    # XXX: replace by a non exception log warning
                    #raise Warning("Dropped already seen instruction %s." % \
                    #        (instruction,))

        # install stage1
        for stack in stacks.stage1.values():
            instruction = stack[-1]
            instruction(dct, Bases(bases))

        # build the class and return it
        return type.__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)

        if dct.has_key('__plumbing__'):
            # install stage2
            stacks = Stacks(dct)
            for stack in stacks.stage2.values():
                instruction = stack[-1]
                instruction(cls)
