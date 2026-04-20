from __future__ import annotations
from dataclasses import dataclass

from interpreter.datatypes import Value
from interpreter.evaluate import evaluate_expr
from interpreter.exceptions import LambError, LambTypeError, LambRuntimeError
from interpreter.parser import build_ast
from interpreter.tokenizer import tokenize
from interpreter.type_inferencer import type_inference


def lamb(lamb_calc_expr: str) -> Value:
    try:
        tokens = tokenize(raw_string=lamb_calc_expr)
        # print(tokens)
        ast, _ = build_ast(tokens)
        return_type = type_inference(ast=ast)
        result = evaluate_expr(ast=ast)
        return result, return_type, None
    except LambError as error:
        return None, None, error

@dataclass
class LambTest:
    name: str
    lamb_calc: str
    result_expected: type[Value] | None = None
    error_expected: type[LambError] | None = None

    def test(self):
        result_actual, return_type, raised_error = lamb(lamb_calc_expr=self.lamb_calc)
        raised_error_type = type(raised_error) if raised_error else None
        passed = self.result_expected == result_actual and self.error_expected == raised_error_type
        prefix = "[O]" if passed else "[X]"
        test_details = []

        if self.result_expected is not None or return_type is not None:
            test_details.append(f"Result<{return_type}>[e: {self.result_expected}, a: {result_actual}]")
        if self.error_expected is not None or raised_error is not None:
            expected_error_name = self.error_expected.name if self.error_expected else "None"
            raised_error_name = type(raised_error).name if raised_error else "None"
            raised_error_str = str(raised_error) if raised_error else "None"
            test_details.append(f"Error[e: {expected_error_name}, a: {raised_error_name}<{raised_error_str}>]")
        test_detail_str = '\n\t' + '\n\t'.join(test_details) if len(test_details) > 1 else test_details
        test_result = f"{prefix} {self.name} => {test_detail_str}"
        print(test_result)

def main():
    tests = [
        # --- PASSING TESTS ---

        # Basic literals
        LambTest(name="Integer literal", lamb_calc="-5", result_expected=-5),
        LambTest(name="Boolean literal true", lamb_calc="true", result_expected=True),
        LambTest(name="Boolean literal false", lamb_calc="false", result_expected=False),

        # Arithmetic
        LambTest(name="Addition", lamb_calc="3 + 4", result_expected=7),
        LambTest(name="Subtraction", lamb_calc="10 - 3", result_expected=7),
        LambTest(name="Multiplication", lamb_calc="3 * 4", result_expected=12),
        LambTest(name="Nested arithmetic precedence", lamb_calc="2 + 3 * 4", result_expected=14),
        LambTest(name="Parenthesized arithmetic", lamb_calc="(2 + 3) * 4", result_expected=20),

        # Comparisons
        LambTest(name="Less than true", lamb_calc="3 < 4", result_expected=True),
        LambTest(name="Less than false", lamb_calc="4 < 3", result_expected=False),
        LambTest(name="Greater than", lamb_calc="5 > 2", result_expected=True),
        LambTest(name="Equality int match", lamb_calc="3 == 3", result_expected=True),
        LambTest(name="Equality int no match", lamb_calc="3 == 4", result_expected=False),
        LambTest(name="Equality bool", lamb_calc="true == false", result_expected=False),

        # If expressions
        LambTest(name="If true branch", lamb_calc="if true then 1 else 2", result_expected=1),
        LambTest(name="If false branch", lamb_calc="if false then 1 else 2", result_expected=2),
        LambTest(name="If bool branches", lamb_calc="if true then false else true", result_expected=False),
        LambTest(name="If with comparison condition", lamb_calc="if 3 < 5 then 10 else 20", result_expected=10),
        LambTest(name="Nested if", lamb_calc="if true then if false then 1 else 2 else 3", result_expected=2),

        # Let bindings
        LambTest(name="Let int binding", lamb_calc="let x = 5 in x + 1", result_expected=6),
        LambTest(name="Let shadows outer", lamb_calc="let x = 5 in let x = 10 in x", result_expected=10),
        LambTest(name="Let nested", lamb_calc="let x = 10 in let y = 5 in let z = 2 in x + y * z", result_expected=20),

        # Functions and closures
        LambTest(name="Identity function int", lamb_calc="let f = fn x => x + 1 in f 3", result_expected=4),
        LambTest(name="Curried addition", lamb_calc="let add = fn x => fn y => x + y in add 3 4", result_expected=7),
        LambTest(name="Partial application", lamb_calc="let add = fn x => fn y => x + y in let add5 = add 5 in add5 10",
                 result_expected=15),
        LambTest(name="Closure captures outer scope", lamb_calc="let n = 7 in let add_n = fn x => x + n in add_n 3",
                 result_expected=10),
        LambTest(name="Closure scope not polluted",
                 lamb_calc="let n = 7 in let add_n = fn x => x + n in let n = 100 in add_n 3", result_expected=10),
        LambTest(name="Higher order compose",
                 lamb_calc="let compose = fn f => fn g => fn x => f (g x) in let add3 = fn x => x + 3 in let mul2 = fn x => x * 2 in compose add3 mul2 5",
                 result_expected=13),
        LambTest(name="Nested function calls",
                 lamb_calc="let x = 3 in let func = fn y => fn z => (z + y + 3) in func (x + 3) 4", result_expected=13),

        # Recursive tests
        LambTest(name="Basic Factorial",
                 lamb_calc="letrec factorial = fn n => if n == 0 then 1 else n * (factorial (n - 1)) in factorial 5",
                 result_expected=120),
        LambTest(name="Power Function",
                 lamb_calc="letrec sum = fn n => if n == 0 then 0 else n + (sum (n - 1)) in sum 10",
                 result_expected=55),
        LambTest(name="Fibonacci",
                 lamb_calc="letrec fib = fn n => if n <= 1 then n else (fib (n - 1)) + (fib (n - 2)) in fib 10",
                 result_expected=55),
        LambTest(name="Recursive with negatives",
                 lamb_calc="letrec f = fn n => if n == 0 then 0 else n + f (n - -1) in f (-5)",
                 result_expected=-15),
        # --- FAILING TESTS ---

        # Arithmetic type errors
        LambTest(name="Add bool to int", lamb_calc="true + 1", error_expected=LambTypeError),
        LambTest(name="Add int to bool", lamb_calc="1 + true", error_expected=LambTypeError),
        LambTest(name="Multiply bools", lamb_calc="true * false", error_expected=LambTypeError),
        LambTest(name="Subtract bool from int", lamb_calc="5 - true", error_expected=LambTypeError),
        LambTest(name="Let shadows outer (type change)", lamb_calc="let x = 5 in let x = true in x + 1", error_expected=LambTypeError),

        # If type errors
        LambTest(name="If branch mismatch int bool", lamb_calc="if true then 1 else false",
                 error_expected=LambTypeError),
        LambTest(name="If branch mismatch bool int", lamb_calc="if true then false else 1",
                 error_expected=LambTypeError),
        LambTest(name="If condition is int", lamb_calc="if 1 then 2 else 3", error_expected=LambTypeError),
        LambTest(name="Nested if branch mismatch", lamb_calc="if true then if false then 1 else true else 3",
                 error_expected=LambTypeError),

        # Comparison type errors
        LambTest(name="Order compare int and bool", lamb_calc="1 < true", error_expected=LambTypeError),
        LambTest(name="Order compare bool and int", lamb_calc="true > 1", error_expected=LambTypeError),
        LambTest(name="Equality int and bool", lamb_calc="1 == true", error_expected=LambTypeError),

        # Application type errors
        LambTest(name="Apply int as function", lamb_calc="let x = 5 in x 3", error_expected=LambTypeError),
        LambTest(name="Pass bool to int function", lamb_calc="let f = fn x => x + 1 in f true",
                 error_expected=LambTypeError),
        LambTest(name="Pass int to bool function", lamb_calc="let f = fn x => if x then 1 else 2 in f 5",
                 error_expected=LambTypeError),
        LambTest(name="Wrong arg type in curried function", lamb_calc="let add = fn x => fn y => x + y in add true 3",
                 error_expected=LambTypeError),

        # Self application
        LambTest(name="Self application in let", lamb_calc="let f = fn x => x x in f 3", error_expected=LambTypeError),
        LambTest(name="Direct self application", lamb_calc="(fn x => x x) 5", error_expected=LambTypeError),

        # Function used with wrong type after being correctly typed
        LambTest(name="Polymorphic misuse", lamb_calc="let f = fn x => x + 1 in if f 3 == 4 then f true else 2",
                 error_expected=LambTypeError),

        LambTest(name="Stack Overflow / Infinite Recursion",
                 lamb_calc="letrec f = fn n => if n == 0 then 0 else n + f (n - -1) in f (5)",
                 error_expected=LambRuntimeError),

    ]

    for test in tests:
        test.test()

if __name__ == "__main__":
    main()