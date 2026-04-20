from __future__ import annotations

from dataclasses import dataclass
import itertools
import string
from typing import Any, Generator, TypeVar

from interpreter.predicates import (
    is_identifier, is_bool, is_int, is_prioritized_expr, is_func_decl, is_let, is_if, is_comp_expr, is_int_type,
    is_bool_type, is_func_type, is_type_variable, is_let_rec
)
from interpreter.datatypes import (
    Expr,
    FuncDeclExpr,
    LetExpr,
    IfExpr,
    CompExpr,
    AddExpr,
    MulExpr,
    AppExpr,
    Atom,
    ChainedAddExpr,
    ChainedMulExpr,
    ChainedAppExpr,
    BooleanOperations, TypeVariable, Type, BoolType, IntType, FuncType, FinalType
)
from interpreter.exceptions import LambInternalError, LambTypeError


def type_var_generator_func():
    for length in itertools.count(1):
        for combo in itertools.product(string.ascii_lowercase, repeat=length):
            yield "'" + "".join(combo)


class TypeVariableGenerator:
    _generator: Generator[str, Any, None]

    def __init__(self):
        self._generator = type_var_generator_func()

    def generate(self):
        next_name = next(self._generator)
        return TypeVariable(next_name)


def occurs_in(left_type: TypeVariable, right_type: Type):
    if is_bool_type(right_type) or is_int_type(right_type):
        return False
    if is_func_type(right_type):
        return (
                occurs_in(left_type=left_type, right_type=right_type.param_type) or
                occurs_in(left_type=left_type, right_type=right_type.return_type)
        )
    if is_type_variable(right_type):
        return left_type == right_type

    error_msg = f"Invalid left type provided for occurs in check: {left_type}"
    raise LambInternalError(error_msg)


def infer_expr_type(ast: Expr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    if is_func_decl(ast):
        return infer_func_decl_type(ast=ast, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    if is_let(ast):
        return infer_let_type(ast=ast, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    if is_let_rec(ast):
        return infer_let_rec_type(ast=ast, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    if is_if(ast):
        return infer_if_type(ast=ast, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    if is_comp_expr(ast):
        return infer_comp_type(ast=ast, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)

    error_msg = f"Type evaluation at the expression level failed to find a valid AST Node: {type(ast)}"
    raise LambInternalError(error_msg)


def infer_func_decl_type(ast: FuncDeclExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    new_param_type_variable = type_var_generator.generate()
    local_env = env.copy()
    local_env[ast.param.name] = new_param_type_variable
    body_type = infer_expr_type(ast=ast.body_expr, env=local_env, inferred_type=inferred_type, type_var_generator=type_var_generator)

    return FuncType(
        param_type=new_param_type_variable,
        return_type=body_type,
    )


def infer_let_type(ast: LetExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    local_env = env.copy()
    identifier_type = infer_expr_type(ast.value, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    local_env[ast.identifier.name] = identifier_type

    return infer_expr_type(ast.body_expr, env=local_env, inferred_type=inferred_type, type_var_generator=type_var_generator)


def infer_let_rec_type(ast: LetExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    rec_type_var: TypeVariable = type_var_generator.generate()
    local_env = env.copy()
    local_env[ast.identifier.name] = rec_type_var
    identifier_type = infer_expr_type(ast.value, env=local_env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    inferred_type.append([rec_type_var, identifier_type])
    return infer_expr_type(ast.body_expr, env=local_env, inferred_type=inferred_type, type_var_generator=type_var_generator)


def infer_if_type(ast: IfExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    bool_type = infer_expr_type(ast.bool_expr, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    then_type = infer_expr_type(ast.then_expr, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)
    else_type = infer_expr_type(ast.else_expr, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)

    inferred_type.append([bool_type, BoolType()])
    if (
            (is_type_variable(then_type) and occurs_in(then_type, else_type)) or
            (is_type_variable(else_type) and occurs_in(else_type, then_type))
    ):
        raise LambTypeError(f"Infinite Type: {then_type} := {else_type}")
    inferred_type.append([then_type, else_type])

    return then_type


def infer_comp_type(ast: CompExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    left_hand_type = infer_add_expr_type(ast.add_expr, env=env, inferred_type=inferred_type, type_var_generator=type_var_generator)

    if ast.chained_expr is not None:
        right_hand_type = infer_add_expr_type(
            ast.chained_expr.add_expr,
            env=env,
            inferred_type=inferred_type,
            type_var_generator=type_var_generator
        )

        if ast.chained_expr.comp_op == BooleanOperations.EQUALITY:
            if (
                (is_type_variable(left_hand_type) and occurs_in(left_hand_type, right_hand_type)) or
                (is_type_variable(right_hand_type) and occurs_in(right_hand_type, left_hand_type))
            ):
                raise LambTypeError(f"Infinite Type: {left_hand_type} := {right_hand_type}")
            inferred_type.append([left_hand_type, right_hand_type])
        else:
            inferred_type.append([left_hand_type, IntType()])
            inferred_type.append([right_hand_type, IntType()])

        return BoolType()
    return left_hand_type


def infer_add_expr_type(ast: AddExpr | ChainedAddExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    left_hand_mul_type = infer_mul_expr_type(
        ast=ast.mul_expr,
        env=env,
        inferred_type=inferred_type,
        type_var_generator=type_var_generator
    )

    right_hand_side = ast.chained_expr
    while right_hand_side is not None:
        right_hand_mul_type = infer_mul_expr_type(
            ast=right_hand_side.mul_expr,
            env=env,
            inferred_type=inferred_type,
            type_var_generator=type_var_generator
        )

        inferred_type.append([left_hand_mul_type, IntType()])
        inferred_type.append([right_hand_mul_type, IntType()])

        left_hand_mul_type = right_hand_mul_type
        right_hand_side = right_hand_side.chained_expr

    return left_hand_mul_type if ast.chained_expr is None else IntType()


def infer_mul_expr_type(ast: MulExpr | ChainedMulExpr, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    left_hand_app_type = infer_app_expr_type(
        ast=ast.app_expr,
        env=env,
        inferred_type=inferred_type,
        type_var_generator=type_var_generator
    )

    right_hand_side = ast.chained_expr
    while right_hand_side is not None:
        right_hand_app_type = infer_app_expr_type(
            ast=right_hand_side.app_expr,
            env=env,
            inferred_type=inferred_type,
            type_var_generator=type_var_generator
        )

        inferred_type.append([left_hand_app_type, IntType()])
        inferred_type.append([right_hand_app_type, IntType()])

        left_hand_app_type = right_hand_app_type
        right_hand_side = right_hand_side.chained_expr

    return left_hand_app_type if ast.chained_expr is None else IntType()


def infer_app_expr_type(
        ast: AppExpr | ChainedAppExpr,
        env: dict[str, Type],
        inferred_type: list[list[Type]],
        type_var_generator: TypeVariableGenerator
) -> Type:
    left_hand_atom_type = infer_atom_type(
        ast=ast.atom,
        env=env,
        inferred_type=inferred_type,
        type_var_generator=type_var_generator
    )

    right_hand_side = ast.chained_expr
    while right_hand_side is not None:
        right_hand_atom_type = infer_atom_type(
            ast=right_hand_side.atom,
            env=env,
            inferred_type=inferred_type,
            type_var_generator=type_var_generator
        )
        if is_func_type(left_hand_atom_type):
            if (
                (is_type_variable(left_hand_atom_type.param_type) and occurs_in(left_hand_atom_type.param_type, right_hand_atom_type)) or
                (is_type_variable(right_hand_atom_type) and occurs_in(right_hand_atom_type, left_hand_atom_type.param_type))
            ):
                raise LambTypeError(f"Infinite Type: {left_hand_atom_type.param_type} := {right_hand_atom_type}")
            inferred_type.append([left_hand_atom_type.param_type, right_hand_atom_type])
            left_hand_atom_type = left_hand_atom_type.return_type
        elif is_type_variable(left_hand_atom_type) and is_identifier(ast.atom):
            if occurs_in(left_hand_atom_type, right_hand_atom_type):
                raise LambTypeError(f"Infinite Type: {left_hand_atom_type} := {right_hand_atom_type}")

            new_func_type = FuncType(
                param_type=right_hand_atom_type,
                return_type=type_var_generator.generate()
            )

            inferred_type.append([left_hand_atom_type, new_func_type])

            left_hand_atom_type = new_func_type.return_type
        else:
            error_msg = f"Primitive int and bool are not callable: {left_hand_atom_type} ({right_hand_atom_type})"
            raise LambTypeError(error_msg)
        right_hand_side = right_hand_side.chained_expr

    return left_hand_atom_type


def infer_atom_type(ast: Atom, env: dict[str, Type], inferred_type: list[list[Type]], type_var_generator: TypeVariableGenerator) -> Type:
    if is_identifier(ast):
        return env[ast.name]
    if is_int(ast):
        return IntType()
    if is_bool(ast):
        return BoolType()
    if is_prioritized_expr(ast):
        return infer_expr_type(
            ast.expr,
            env=env,
            inferred_type=inferred_type,
            type_var_generator=type_var_generator
        )

    error_msg = f"Type evaluation at the atom level failed to find a valid AST Node: {type(ast)}"
    raise LambInternalError(error_msg)


def perform_substitution(original_type: Type, sub_var: TypeVariable, sub_type: Type) -> Type:
    if is_func_type(original_type):
        if original_type.param_type == sub_var:
            original_type.param_type = sub_type
        original_type.return_type = perform_substitution(
            original_type=original_type.return_type,
            sub_var=sub_var,
            sub_type=sub_type
        )
    elif original_type == sub_var:
        return sub_type
    return original_type


def substitute_inferred_type(
        sub_var: TypeVariable,
        sub_type: Type,
        inferred_types: list[list[Type]],
        substitutions: dict[TypeVariable, Type]
) -> None:
    substitutions[sub_var] = sub_type
    for idx, (left, right) in enumerate(inferred_types):
        inferred_types[idx] = [
            perform_substitution(original_type=left, sub_var=sub_var, sub_type=sub_type),
            perform_substitution(original_type=right, sub_var=sub_var, sub_type=sub_type)
        ]


def unify_inferred_type(left: Type, right: Type, inferred_types: list[list[Type]], substitutions: dict[TypeVariable, Type]):
    if (
            (is_int_type(left) and is_int_type(right)) or
            (is_bool_type(left) and is_bool_type(right))
    ):
        return
    if (
            (is_int_type(left) and is_bool_type(right)) or
            (is_bool_type(left) and is_int_type(right))
    ):
        error_msg = f"Failed to unify types: {left} <> {right}"
        raise LambTypeError(error_msg)
    elif (
            (is_int_type(left) or is_bool_type(left) or is_func_type(left)) and is_type_variable(
        right)
    ):
        substitute_inferred_type(sub_var=right, sub_type=left, inferred_types=inferred_types, substitutions=substitutions)
    elif (is_int_type(right) or is_bool_type(right) or is_func_type(right)) and is_type_variable(left):
        substitute_inferred_type(sub_var=left, sub_type=right, inferred_types=inferred_types, substitutions=substitutions)
    elif (
            is_type_variable(left) and is_type_variable(right)
    ):
        substitute_inferred_type(sub_var=right, sub_type=left, inferred_types=inferred_types, substitutions=substitutions)
    elif is_func_type(left) and is_func_type(right):
        # Check that param = other or resolve it
        unify_inferred_type(left=left.param_type, right=right.param_type, substitutions=substitutions,
                            inferred_types=inferred_types)
        unify_inferred_type(left=left.return_type, right=right.return_type, substitutions=substitutions,
                            inferred_types=inferred_types)
    else:
        error_msg = f"Failed to unify types: {left} <> {right}"
        raise LambTypeError(error_msg)


def unification(inferred_types: list[list[Type]]):
    substitutions = {}
    for (left, right) in inferred_types:
        unify_inferred_type(left=left, right=right, inferred_types=inferred_types, substitutions=substitutions)
    return substitutions


def apply_substitution(return_type: Type, substitutions: dict[TypeVariable, Type]) -> FinalType:
    if is_int_type(return_type) or is_bool_type(return_type):
        return return_type
    if is_func_type(return_type):
        return FuncType(
            param_type=apply_substitution(return_type=return_type.param_type, substitutions=substitutions),
            return_type=apply_substitution(return_type=return_type.return_type, substitutions=substitutions),
        )
    if is_type_variable(return_type):
        if return_type not in substitutions:
            error_msg = f"Failed to substitute type: {return_type}, substitutions: {substitutions}"
            raise LambTypeError(error_msg)
        return apply_substitution(return_type=substitutions[return_type], substitutions=substitutions)

    error_msg = f"Unification during the substitution phase failed due to return_type being of type: {type(return_type)}"
    raise LambInternalError(error_msg)


def type_inference(ast: Expr) -> FinalType:
    type_var_generator = TypeVariableGenerator()
    env: dict[str, Type] = {}
    inferred_types: list[list[Type]] = []
    return_type = infer_expr_type(ast=ast, env=env, inferred_type=inferred_types, type_var_generator=type_var_generator)
    substitutions = unification(inferred_types=inferred_types)
    return apply_substitution(return_type=return_type, substitutions=substitutions)