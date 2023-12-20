
class PyRopeError(Exception):
    pass


class IllPosedError(PyRopeError):
    pass


class ValidationError(PyRopeError):

    def __init__(self, message, ifield=None):
        self.ifield = ifield
        super().__init__(message)
