
class LambError(Exception):
    name = "LambError"

class LambSyntaxError(LambError):
    name = "LambSyntaxError"

class LambSemanticError(LambError):
    name = "LambSemanticError"

class LambRuntimeError(LambError):
    name = "LambRuntimeError"

class LambInternalError(LambError):
    name = "LambInternalError"

class LambTypeError(LambError):
    name = "LambTypeError"