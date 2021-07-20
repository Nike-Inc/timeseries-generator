class FactorAlreadyExistsError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class DuplicateNameError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
