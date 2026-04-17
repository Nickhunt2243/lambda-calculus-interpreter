from __future__ import annotations
from interpreter.predicates import (
 is_bool, is_int, is_identifier, is_left_paren
)
from interpreter.exceptions import LambSemanticError
from interpreter.datatypes import Token, Keyword, Arrow, LParen, EqualSign, BooleanOperations, AdditiveOperations, \
    MultiplicativeOperations, IntegerLiteral, BooleanLiteral, Identifier, Expr, FuncDeclExpr, LetExpr, IfExpr, CompExpr, \
    ChainedCompExpr, ChainedAddExpr, AddExpr, MulExpr, ChainedMulExpr, AppExpr, ChainedAppExpr, Atom, PrioritizedExpr


INVALID_EXPR_ERROR = """
Invalid expression. Expected expression syntax:
<expr>     ::= fn <identifier> => <expr>
            | let <identifier> = <expr> in <expr>  
            | if <expr> then <expr> else <expr>
            | <comp_expr>
"""
INVALID_FUNC_DECL_EXPR_ERROR = "Incomplete func declaration. Syntax expected: fn <identifier> => <expr>"
INVALID_LET_EXPR_ERROR = "Incomplete Let statement. Syntax expected: let <identifier> = <expr> in <expr>"
INVALID_IF_EXPR_ERROR = "Incomplete if statement. Syntax expected: if <expr> then <expr> else <expr>"

def build_expr(tokens: list[Token], idx: int) -> (Expr, int):
    if idx >= len(tokens):
        raise LambSemanticError()
    if tokens[idx] == Keyword.FN:
        return build_function_decl(tokens, idx)
    elif tokens[idx] == Keyword.LET:
        return build_let(tokens, idx)
    elif tokens[idx] == Keyword.IF:
        return build_if(tokens, idx)
    elif (
        is_identifier(tokens[idx]) or
        is_int(tokens[idx]) or
        is_bool(tokens[idx]) or
        is_left_paren(tokens[idx])
    ):
        return build_comp(tokens, idx)
    else:
        raise LambSemanticError(INVALID_EXPR_ERROR)


def build_function_decl(tokens: list[Token], idx: int) -> (FuncDeclExpr, int):
    if idx + 3 >= len(tokens):
        raise LambSemanticError(INVALID_FUNC_DECL_EXPR_ERROR)
    if tokens[idx] != Keyword.FN:
        raise LambSemanticError(f"Expected fn, actual: {tokens[idx]}")
    if not isinstance(tokens[idx + 1], Identifier):
        raise LambSemanticError(f"Expected identifier, received: {tokens[idx+1]}.")
    if not isinstance(tokens[idx + 2], Arrow):
        raise LambSemanticError(f"Expected =>, received: {tokens[idx+2]}.")

    body_expr, next_idx = build_expr(tokens, idx + 3)

    return FuncDeclExpr(
        param=tokens[idx+1],
        body_expr=body_expr
    ), next_idx


def build_let(tokens: list[Token], idx: int) -> (LetExpr, int):
    if idx + 3 >= len(tokens):
       raise LambSemanticError(INVALID_LET_EXPR_ERROR)
    if not isinstance(tokens[idx + 1], Identifier):
        raise LambSemanticError(f"Expected identifier, received: {tokens[idx+1]}.")
    if not isinstance(tokens[idx + 2], EqualSign):
        raise LambSemanticError(f"Expected =, received: {tokens[idx+2]}.")
    
    value, next_idx = build_expr(tokens=tokens, idx=idx + 3)

    if next_idx + 1 >= len(tokens):
        raise LambSemanticError(INVALID_LET_EXPR_ERROR)

    if tokens[next_idx] != Keyword.IN:
        raise LambSemanticError(f"Expected in, received: {tokens[next_idx]}.")

    body_expr, next_idx = build_expr(tokens=tokens, idx=next_idx + 1)
    return LetExpr(
        identifier=tokens[idx+1],
        value=value,
        body_expr=body_expr,
    ), next_idx




def build_if(tokens: list[Token], idx: int) -> (IfExpr, int):
    bool_expr, then_idx = build_expr(tokens=tokens, idx=idx + 1)
    if then_idx >= len(tokens):
        raise LambSemanticError(INVALID_IF_EXPR_ERROR)
    if tokens[then_idx] != Keyword.THEN:
        raise LambSemanticError(f"Expected then, received: {tokens[then_idx]}.")
    then_expr, else_idx = build_expr(tokens=tokens, idx=then_idx + 1)
    if else_idx >= len(tokens):
        raise LambSemanticError(INVALID_IF_EXPR_ERROR)
    if tokens[else_idx] != Keyword.ELSE:
        raise LambSemanticError(f"Expected else, received: {tokens[then_idx]}.")
    else_expr, last_idx = build_expr(tokens=tokens, idx=else_idx + 1)

    return IfExpr(
        bool_expr=bool_expr,
        then_expr=then_expr,
        else_expr=else_expr,
    ), last_idx


def build_comp(tokens: list[Token], idx: int) -> (CompExpr, int):
    additive_expr, chained_idx = build_additive(tokens, idx)
    chained_comp, next_idx = build_chained_comp(tokens, chained_idx)

    return CompExpr(
        add_expr=additive_expr,
        chained_expr=chained_comp
    ), next_idx


def build_chained_comp(tokens: list[Token], idx: int) -> (ChainedCompExpr, int):
    if idx >= len(tokens) or not isinstance(tokens[idx], BooleanOperations):
        return None, idx

    additive_expr, next_idx = build_additive(tokens, idx + 1)

    return ChainedCompExpr(
        comp_op=tokens[idx],
        add_expr=additive_expr,
    ), next_idx


def build_additive(tokens: list[Token], idx: int) -> (AddExpr, int):
    multiplicative_expr, chained_idx = build_multiplicative(tokens, idx)
    chained_expr, next_idx = build_chained_additive(tokens, chained_idx)
    
    return AddExpr(
        mul_expr=multiplicative_expr,
        chained_expr=chained_expr
    ), next_idx


def build_chained_additive(tokens: list[Token], idx: int) -> (ChainedAddExpr, int):
    if idx >= len(tokens) or not isinstance(tokens[idx], AdditiveOperations):
        return None, idx

    multiplicative_expr, chained_idx = build_multiplicative(tokens, idx+1)
    chained_expr, next_idx = build_chained_additive(tokens, chained_idx)
    return ChainedAddExpr(
        additive_operation=tokens[idx],
        mul_expr=multiplicative_expr,
        chained_expr=chained_expr,
    ), next_idx


def build_multiplicative(tokens: list[Token], idx: int) -> (MulExpr, int):
    application_expr, chained_idx = build_application(tokens, idx)
    additional_multiplicative_expr, next_idx = build_chained_multiplicative(tokens, chained_idx)

    return MulExpr(
        app_expr=application_expr,
        chained_expr=additional_multiplicative_expr
    ), next_idx


def build_chained_multiplicative(tokens: list[Token], idx: int) -> (ChainedMulExpr, int):
    if idx >= len(tokens) or not isinstance(tokens[idx], MultiplicativeOperations):
        return None, idx

    application_expr, chained_idx = build_application(tokens, idx + 1)
    additional_multiplicative_expr, next_idx = build_chained_multiplicative(tokens, chained_idx)
    
    return ChainedMulExpr(
        multiplicative_operation=tokens[idx],
        app_expr=application_expr,
        chained_expr=additional_multiplicative_expr,
    ), next_idx


def build_application(tokens: list[Token], idx: int) -> (AppExpr, int):
    if (
        not isinstance(tokens[idx], Identifier) and
        not isinstance(tokens[idx], IntegerLiteral) and
        not isinstance(tokens[idx], BooleanLiteral) and
        not isinstance(tokens[idx], LParen)
    ):
        raise LambSemanticError(f"Failed to build application, received: {tokens[idx]}.")
    atom, chained_idx = build_atom(tokens, idx)
    expr, next_idx = build_chained_application(tokens, chained_idx)
    return AppExpr(
        atom=atom,
        chained_expr=expr
    ), next_idx


def build_chained_application(tokens: list[Token], idx: int) -> (ChainedAppExpr, int):
    if idx >= len(tokens) or (
        not isinstance(tokens[idx], Identifier) and
        not isinstance(tokens[idx], IntegerLiteral) and
        not isinstance(tokens[idx], BooleanLiteral) and
        not isinstance(tokens[idx], LParen)
    ):
        return None, idx
    atom, chained_idx = build_atom(tokens, idx)
    expr, next_idx = build_chained_application(tokens, chained_idx)
    return ChainedAppExpr(
        atom=atom,
        chained_expr=expr
    ), next_idx


def build_atom(tokens: list[Token], idx: int) -> (Atom, int):
    if (
            isinstance(tokens[idx], Identifier) or
            isinstance(tokens[idx], BooleanLiteral) or
            isinstance(tokens[idx], IntegerLiteral)
    ):
        return tokens[idx], idx + 1
    elif isinstance(tokens[idx], LParen):
        expr, next_idx = build_expr(tokens, idx + 1)
        return PrioritizedExpr(
            expr=expr
        ), next_idx + 1
    else:
        raise LambSemanticError(f"Failed to build atom, received: {tokens[idx]}.")


def build_ast(tokens: list[Token]) -> (Expr, int):
    return build_expr(tokens, 0)