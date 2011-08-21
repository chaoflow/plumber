class PlumbingCollision(RuntimeError):
    def __init__(self, name, left=None, right=None):
        msg = "\n".join([
            "'%s'",
            "    %s",
            "  collides with:",
            "    %s",
            ]) % (name, left, right) if right else name
        super(PlumbingCollision, self).__init__(msg)
