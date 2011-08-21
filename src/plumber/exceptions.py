class PlumbingCollision(RuntimeError):
    def __init__(self, name, left, right):
        msg = "\n".join([
            "'%s'",
            "    %s",
            "  collides with:",
            "    %s",
            ]) % (name, left, right)
        super(PlumbingCollision, self).__init__(msg)
