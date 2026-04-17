from typing import Any

from interpreter.datatypes import IntegerLiteral, BooleanLiteral, Closure, Identifier, LParen, PrioritizedExpr, \
    FuncDeclExpr, LetExpr, IfExpr, CompExpr, AddExpr, MulExpr, AppExpr, Atom, TypeVariable, FuncType, IntType, BoolType


# Predicates
def is_white_space(x: str):
    return x == " " or x == "\n" or x == "\t"
def is_int(x: Any):
    return isinstance(x, int) or isinstance(x, IntegerLiteral)


def is_bool(x: Any):
    return isinstance(x, bool) or isinstance(x, BooleanLiteral)


def is_closure(x: Any):
    return isinstance(x, Closure)


def is_identifier(x: Any):
    return isinstance(x, Identifier)


def is_left_paren(x: Any):
    return isinstance(x, LParen)


def is_prioritized_expr(x: Any):
    return isinstance(x, PrioritizedExpr)


def is_func_decl(x: Any):
    return isinstance(x, FuncDeclExpr)


def is_let(x: Any):
    return isinstance(x, LetExpr)


def is_if(x: Any):
    return isinstance(x, IfExpr)


def is_comp_expr(x: Any):
    return isinstance(x, CompExpr)


def is_add_expr(x: Any):
    return isinstance(x, AddExpr)


def is_mul_expr(x: Any):
    return isinstance(x, MulExpr)


def is_app_expr(x: Any):
    return isinstance(x, AppExpr)


def is_atom(x: Any):
    return isinstance(x, Atom)


def is_type_variable(x: Any):
    return isinstance(x, TypeVariable)


def is_func_type(x: Any):
    return isinstance(x, FuncType)


def is_int_type(x: Any):
    return isinstance(x, IntType)


def is_bool_type(x: Any):
    return isinstance(x, BoolType)