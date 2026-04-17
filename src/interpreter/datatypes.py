from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

from interpreter.exceptions import LambRuntimeError


# --- Tokenization ---


@dataclass(frozen=True)
class IntegerLiteral:
    value: int

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True)
class BooleanLiteral:
    value: bool

    def __str__(self):
        return str(self.value)


class Keyword(Enum):
    FN = "fn"
    LET = "let"
    IN = "in"
    IF = "if"
    THEN = "then"
    ELSE = "else"


class AdditiveOperations(Enum):
    ADD = "+"
    SUB = "-"


class MultiplicativeOperations(Enum):
    MUL = "*"
    DIV = "/"


class BooleanOperations(Enum):
    EQUALITY = "=="
    LESS_THAN = "<"
    LESS_THAN_EQUAL_TO = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL_TO = ">="


@dataclass(frozen=True)
class EqualSign:
    pass


@dataclass(frozen=True)
class Arrow:
    pass


@dataclass(frozen=True)
class LParen:
    pass


@dataclass(frozen=True)
class RParen:
    pass


@dataclass(frozen=True)
class Identifier:
    name: str

    def __str__(self):
        return self.name


Token = IntegerLiteral \
        | BooleanLiteral \
        | Keyword \
        | AdditiveOperations \
        | MultiplicativeOperations \
        | BooleanOperations \
        | EqualSign \
        | Arrow \
        | LParen \
        | RParen \
        | Identifier


# --- Abstract Syntax Tree ---

@dataclass(frozen=True)
class LetExpr:
    identifier: Identifier
    value: Expr
    body_expr: Expr

    def __str__(self):
        return f"let {self.identifier} = {self.value} in {self.body_expr}"


@dataclass(frozen=True)
class IfExpr:
    bool_expr: Expr
    then_expr: Expr
    else_expr: Expr

    def __str__(self):
        return f"if {self.bool_expr} then {self.then_expr} else {self.else_expr}"


@dataclass(frozen=True)
class Closure:
    param: str
    stack: dict[str, Value]
    expr: Expr


@dataclass(frozen=True)
class FuncDeclExpr:
    param: Identifier
    body_expr: Expr

    def __str__(self):
        return f"fn {self.param} => {self.body_expr}"


@dataclass(frozen=True)
class CompExpr:
    add_expr: AddExpr
    chained_expr: ChainedCompExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.add_expr} {self.chained_expr}"
        return str(self.add_expr)


@dataclass(frozen=True)
class ChainedCompExpr:
    add_expr: AddExpr
    comp_op: BooleanOperations

    def __str__(self):
        return f"{self.comp_op.value} {self.add_expr}"


@dataclass(frozen=True)
class AddExpr:
    mul_expr: MulExpr
    chained_expr: ChainedAddExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.mul_expr} {self.chained_expr}"
        return str(self.mul_expr)


@dataclass(frozen=True)
class ChainedAddExpr:
    mul_expr: MulExpr
    additive_operation: AdditiveOperations
    chained_expr: ChainedAddExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.additive_operation.value} {self.mul_expr} {self.chained_expr}"
        return f"{self.additive_operation.value} {self.mul_expr}"


@dataclass(frozen=True)
class MulExpr:
    app_expr: AppExpr
    chained_expr: ChainedMulExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.app_expr} {self.chained_expr}"
        return str(self.app_expr)


@dataclass(frozen=True)
class ChainedMulExpr:
    app_expr: AppExpr
    multiplicative_operation: MultiplicativeOperations
    chained_expr: ChainedMulExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.multiplicative_operation.value} {self.app_expr} {self.chained_expr}"
        return f"{self.multiplicative_operation.value} {self.app_expr}"


@dataclass(frozen=True)
class AppExpr:
    atom: Atom
    chained_expr: ChainedAppExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.atom} {self.chained_expr}"
        return str(self.atom)


@dataclass(frozen=True)
class ChainedAppExpr:
    atom: Atom
    chained_expr: ChainedAppExpr | None

    def __str__(self):
        if self.chained_expr:
            return f"{self.atom} {self.chained_expr}"
        return str(self.atom)


@dataclass(frozen=True)
class PrioritizedExpr:
    expr: Expr

    def __str__(self):
        return f"( {self.expr} )"


Expr: dataclass = LetExpr | IfExpr | FuncDeclExpr | CompExpr
Atom: dataclass = Identifier | IntegerLiteral | BooleanLiteral | PrioritizedExpr
Value = bool | int | Closure


# --- Type System ---

class TypeVariable:
    name: str

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, o: Any):
        if not isinstance(o, TypeVariable):
            return False

        return self.name == o.name

    def __hash__(self):
        return self.name.__hash__()

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class IntType:

    def __str__(self):
        return "int"


@dataclass(frozen=True)
class BoolType:

    def __str__(self):
        return "bool"


@dataclass
class FuncType:
    """Type of function declaration.

    Purposely left unfrozen as to allow unification in place.
    """
    param_type: Type
    return_type: Type  # Int -> Int, 'a -> 'a, etc.

    def __str__(self):
        return f"{self.param_type} -> {self.return_type}"


Type = TypeVariable | IntType | BoolType | FuncType
FinalType = IntType | BoolType | FuncType