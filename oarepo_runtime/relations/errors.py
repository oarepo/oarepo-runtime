class InvalidRelationError(KeyError):
    def __init__(self, message, related_id, location):
        self.related_id = related_id
        self.location = location
        super().__init__(message)


class MultipleInvalidRelationErrors(Exception):
    """
    Records multiple validation errors of a relation field.
    self.errors is a list of pairs (path, Error)
    """

    def __init__(self, errors):
        super().__init__(
            "; ".join([f"{e[0]}: {type(e[1]).__name__}({e[1]})" for e in errors])
        )
        self.errors = errors
