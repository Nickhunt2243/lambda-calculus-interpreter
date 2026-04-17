from interpreter.predicates import (
 is_bool, is_closure, is_int, is_identifier, is_func_decl, is_let, is_prioritized_expr, is_comp_expr, is_if,
)
from interpreter.datatypes import Value, Expr, LetExpr, Closure, FuncDeclExpr, CompExpr, ChainedCompExpr, \
    BooleanOperations, AddExpr, ChainedAddExpr, AdditiveOperations, MulExpr, ChainedMulExpr, \
    MultiplicativeOperations, IfExpr, AppExpr, ChainedAppExpr, PrioritizedExpr,  \
    Identifier, IntegerLiteral, BooleanLiteral, Atom
from interpreter.exceptions import LambRuntimeError, LambInternalError


def evaluate_expr(ast: Expr, stack: dict[str, Value] | None = None) -> Value:
    if stack is None:
        stack = {}

    if is_func_decl(ast):
        return evaluate_func_decl(ast=ast, stack=stack)
    if is_let(ast):
        return evaluate_let_expr(ast=ast, stack=stack)
    if is_if(ast):
        return evaluate_if_expr(ast=ast, stack=stack)
    if is_comp_expr(ast):
        return evaluate_comp_expr(ast=ast, stack=stack)

    error_msg = f"Unexpected expression during runtime calculation: {type(ast)}"
    raise LambInternalError(error_msg)


def evaluate_let_expr(ast: LetExpr, stack: dict[str, Value]) -> Value:
    local_stack: dict[str, Value] = stack.copy()
    local_stack[ast.identifier.name] = evaluate_expr(ast=ast.value, stack=stack)
    return evaluate_expr(ast=ast.body_expr, stack=local_stack)



def evaluate_if_expr(ast: IfExpr, stack: dict[str, Value]) -> Value:
    if evaluate_expr(ast.bool_expr, stack=stack):
        return evaluate_expr(ast=ast.then_expr, stack=stack)
    else:
        return evaluate_expr(ast=ast.else_expr, stack=stack)


def evaluate_closure(ast: Closure, param_value: Value) -> Value:
    local_stack = ast.stack.copy()
    local_stack[ast.param] = param_value
    return evaluate_expr(ast=ast.expr, stack=local_stack)


def evaluate_func_decl(ast: FuncDeclExpr, stack: dict[str, Value]) -> Value:
    return Closure(
        param=ast.param.name,
        stack=stack,
        expr=ast.body_expr
    )

def evaluate_comp_expr(ast: CompExpr, stack: dict[str, Value]) -> Value:
    left_hand_eval = evaluate_add_expr(ast.add_expr, stack=stack)
    if ast.chained_expr is not None:
        return evaluate_chained_comp_expr(ast=ast.chained_expr, stack=stack, left_hand_side=left_hand_eval)
    return left_hand_eval

def evaluate_chained_comp_expr(ast: ChainedCompExpr,stack: dict[str, Value], left_hand_side: Value) -> Value:
    right_hand_side = evaluate_add_expr(ast=ast.add_expr, stack=stack)
    if is_int(left_hand_side) and is_bool(right_hand_side):
        left_hand_side = left_hand_side != 0
    if is_bool(left_hand_side) and is_int(right_hand_side):
        right_hand_side = right_hand_side != 0

    if is_closure(left_hand_side) and ast.comp_op != BooleanOperations.EQUALITY:
        raise LambRuntimeError("Left hand side of boolean expression cannot be a Closure/function call.")
    if is_closure(right_hand_side) and ast.comp_op != BooleanOperations.EQUALITY:
        raise LambRuntimeError("Left hand side of boolean expression cannot be a Closure/function call.")

    match ast.comp_op:
        case BooleanOperations.EQUALITY:
            return left_hand_side == right_hand_side
        case BooleanOperations.LESS_THAN:
            return left_hand_side < right_hand_side
        case BooleanOperations.LESS_THAN_EQUAL_TO:
            return left_hand_side <= right_hand_side
        case BooleanOperations.GREATER_THAN:
            return left_hand_side > right_hand_side
        case BooleanOperations.GREATER_THAN_EQUAL_TO:
            return left_hand_side >= right_hand_side

def evaluate_add_expr(ast: AddExpr, stack: dict[str, Value]) -> Value:
    left_hand_eval = evaluate_mul_expr(ast=ast.mul_expr, stack=stack)
    if ast.chained_expr is not None:
        return evaluate_chained_add_expr(ast=ast.chained_expr, stack=stack, left_hand_side=left_hand_eval)
    return left_hand_eval


def evaluate_chained_add_expr(ast: ChainedAddExpr, stack: dict[str, Value], left_hand_side: Value) -> Value:
    right_hand_side = evaluate_mul_expr(ast=ast.mul_expr, stack=stack)
    if is_int(left_hand_side) and is_int(right_hand_side):
        result = (
            left_hand_side + right_hand_side
            if ast.additive_operation == AdditiveOperations.ADD
            else left_hand_side - right_hand_side
        )
        if ast.chained_expr is None:
            return result
        else:
            return evaluate_chained_add_expr(
                ast=ast.chained_expr,
                stack=stack,
                left_hand_side=result
            )
    elif (
            (not is_int(left_hand_side) and is_int(right_hand_side)) or
            (is_int(left_hand_side) and not is_int(right_hand_side))
    ):
        raise LambRuntimeError(f"Cannot add or subtract integer and boolean types.")
    else:
        raise LambRuntimeError(f"Cannot add or subtract boolean types.")


def evaluate_mul_expr(ast: MulExpr, stack: dict[str, Value]) -> Value:
    left_hand_eval = evaluate_app_expr(ast=ast.app_expr, stack=stack)
    if ast.chained_expr is not None:
        return evaluate_chained_mul_expr(ast=ast.chained_expr, stack=stack, left_hand_side=left_hand_eval)
    return left_hand_eval


def evaluate_chained_mul_expr(ast: ChainedMulExpr, stack: dict[str, Value], left_hand_side: Value) -> Value:
    right_hand_side = evaluate_app_expr(ast=ast.app_expr, stack=stack)
    if is_int(left_hand_side) and is_int(right_hand_side):
        result = (
            left_hand_side * right_hand_side
            if ast.multiplicative_operation == MultiplicativeOperations.MUL
            else left_hand_side // right_hand_side
        )
        if ast.chained_expr is None:
            return result
        else:
            return evaluate_chained_mul_expr(
                ast=ast.chained_expr,
                stack=stack,
                left_hand_side=result
            )
    elif (
            (not is_int(left_hand_side) and is_int(right_hand_side)) or
            (is_int(left_hand_side) and not is_int(right_hand_side))
    ):
        raise LambRuntimeError(f"Cannot multiply or divide integer and boolean types.")
    else:
        raise LambRuntimeError(f"Cannot multiply or divide boolean types.")


def evaluate_app_expr(ast: AppExpr, stack: dict[str, Value]) -> Value:
    applied_app = evaluate_atom(ast=ast.atom, stack=stack)

    if is_closure(applied_app) and is_identifier(ast.atom):
        if ast.chained_expr is None:
            raise LambRuntimeError(f"Failed to supply parameter to function call: {ast.atom.name}.")

        param_eval = evaluate_chained_app_expr(ast=ast.chained_expr, stack=stack)
        closure_eval = evaluate_closure(ast=applied_app, param_value=param_eval)
        return post_evaluate_chained_app_expr(
            ast=ast.chained_expr,
            stack=stack,
            original_func=ast.atom.name,
            previous_chain_eval=closure_eval
        )
    return applied_app


def evaluate_chained_app_expr(ast: ChainedAppExpr, stack: dict[str, Value]) -> Value:
    return evaluate_atom(ast=ast.atom, stack=stack)


def post_evaluate_chained_app_expr(
    ast: ChainedAppExpr,
    stack: dict[str, Value],
    original_func: str,
    previous_chain_eval: Value
) -> Value:
    if is_closure(previous_chain_eval):

        # Handle function call
        if ast.chained_expr is None:
            return previous_chain_eval
        else:

            param_eval = evaluate_chained_app_expr(ast=ast.chained_expr, stack=stack)
            closure_eval = evaluate_closure(ast=previous_chain_eval, param_value=param_eval)
            return post_evaluate_chained_app_expr(
                ast=ast.chained_expr,
                stack=stack,
                original_func=original_func,
                previous_chain_eval=closure_eval
            )
    return previous_chain_eval


def evaluate_atom(ast: Atom, stack: dict[str, Value]) -> Value:
    if is_int(ast):
        return evaluate_integer(ast=ast)
    if is_bool(ast):
        return evaluate_boolean(ast=ast)
    if is_identifier(ast):
        return evaluate_identifier(ast=ast, stack=stack)
    if is_prioritized_expr(ast):
        return evaluate_prioritized_expr(ast=ast, stack=stack)

    error_msg = f"Invalid Atom type: {type(ast)}"
    raise LambInternalError(error_msg)


def evaluate_identifier(ast: Identifier, stack: dict[str, Value]) -> Value:
    if ast.name not in stack:
        raise LambRuntimeError(f"Variable {ast.name} used prior to declaration.")

    return stack[ast.name]


def evaluate_integer(ast: IntegerLiteral) -> Value:
    return ast.value


def evaluate_boolean(ast: BooleanLiteral) -> Value:
    return ast.value


def evaluate_prioritized_expr(ast: PrioritizedExpr, stack: dict[str, Value]) -> Value:
    return evaluate_expr(ast=ast.expr, stack=stack)