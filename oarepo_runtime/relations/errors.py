class InvalidRelationError(KeyError):
    def __init__(self, message, related_id, location):
        self.related_id = related_id
        self.location = location
        super().__init__(message)
