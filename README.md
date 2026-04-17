# Lambda Calculus Interpreter

A small interpreter for a minimal functional language grounded in the untyped
lambda calculus, extended with a Hindley-Milner type inferencer. Built to
demonstrate core programming language implementation concepts: lexical
analysis, recursive descent parsing, environment-based evaluation, closure
semantics, and constraint-based type inference.

---

## Quick Start

```bash
$ cd src
$ python main.py
```

The interpreter runs a built-in test suite that exercises both the evaluator
and the type inferencer across passing and failing cases. Each test prints
its name, inferred type, expected result, and actual result.

To use the interpreter programmatically:

```python
from interpreter.evaluate import evaluate_expr
from interpreter.parser import build_ast
from interpreter.tokenizer import tokenize
from interpreter.type_inferencer import type_inference

expression = "let add = fn x => fn y => x + y in add 3 4"

tokens = tokenize(raw_string=expression)
ast, _ = build_ast(tokens)
inferred_type = type_inference(ast=ast)   # int
result = evaluate_expr(ast=ast)           # 7
```

or 

```bash
$ ./lamb "let add = fn x => fn y => x + y in add 3 4"
7 : int
```

---

## The Language

The language is expression-oriented — every program is a single expression
that reduces to a value. There are no statements, no mutation, and no
implicit sequencing. Computation happens entirely through function application
and let bindings.

The language supports integer and boolean literals, binary arithmetic and
comparison operators, conditionals, anonymous functions (lambdas), function
application, and let bindings for naming values. Functions are first-class
values: they can be passed as arguments, returned from other functions, and
stored in bindings. All functions take exactly one argument. Multi-argument
functions are expressed through currying — a function that appears to take
two arguments is actually a function that takes one argument and returns
another function that takes the second.

Scoping is lexical. A variable always resolves to the binding that was in
scope where the function was defined, not where it was called. This is the
foundation of closure semantics.

The formal grammar is defined in EBNF.md.

---

## Example Programs

**Basic arithmetic and let bindings**

```
let x = 10 in let y = 5 in x + y
```

Evaluates to `15`. Let bindings are not variable assignments — they are
expressions that introduce a name into scope for the duration of their body.

**Curried addition**

```
let add = fn x => fn y => x + y in add 3 4
```

Evaluates to `7`. Multi-argument functions are just functions returning
functions — currying is not syntactic sugar here, it is the actual evaluation
model. The type inferencer infers `add : int -> int -> int` without any
annotations.

**Closures capturing outer scope**

```
let make_adder = fn n => fn x => x + n in
let add5 = make_adder 5 in
add5 10
```

Evaluates to `15`. The inner function closes over `n` from the outer scope.
When `make_adder 5` returns, the value `5` is captured inside the returned
closure. Later calls to `add5` can still access `n` even though `make_adder`
has already finished executing. This is closure semantics in action.

**Conditionals**

```
let abs = fn x => if x < 0 then 0 - x else x in abs (0 - 7)
```

Evaluates to `7`. Conditionals are expressions, not statements — both
branches must be present and both must produce values of the same type.
The type inferencer enforces this: `if true then 1 else false` is a type
error because the branches have incompatible types.

---

## Architecture

The interpreter is a four-stage pipeline:

```
Source text
    │
    ▼
Tokenizer          token stream
    │
    ▼
Parser             abstract syntax tree (untyped)
    │
    ▼
Type Inferencer    inferred type or LambTypeError
    │
    ▼
Evaluator          value (int | bool | Closure)
```

Each stage has a clearly defined input and output type. Errors are caught
and reported at the stage where they occur: the tokenizer reports unrecognized
characters, the parser reports malformed syntax, the type inferencer reports
type violations before any execution occurs, and the evaluator reports
runtime errors such as unbound variables.

### Source layout

```
src/
  main.py                    entry point and test suite
  interpreter/
    datatypes.py             AST node types and type system data structures
    tokenizer.py             lexical analysis
    parser.py                recursive descent parser
    evaluate.py              tree-walking evaluator
    type_inferencer.py       Hindley-Milner type inference and unification
    predicates.py            isinstance helpers used across modules
    exceptions.py            error hierarchy
```

---

## Tokenizer

The tokenizer performs lexical analysis — converting raw source text into a
flat sequence of typed tokens. It works character by character, recognizing
integer literals, boolean keywords, identifiers, reserved words, operators,
arrows, equals signs, and parentheses.

The tokenizer is hand-written without regular expression libraries, scanning
the source in a single pass. Multi-character tokens such as `=>`, `==`, `<=`,
and `>=` require lookahead — the tokenizer cannot determine the correct token
until it reads the second character. This is the standard NFA-based behavior
described in compiler literature: the tokenizer follows all possible paths
simultaneously until sufficient input resolves the ambiguity.

Whitespace is consumed and discarded between tokens. Identifiers are
distinguished from keywords by checking the recognized word against the
reserved word set after the full word has been scanned.

---

## Parser

The parser performs syntactic analysis — consuming the token stream and
constructing an abstract syntax tree that represents the grammatical
structure of the program.

The parser is implemented as a recursive descent parser. Each grammatical
rule in the language corresponds directly to a parsing function. The parser
maintains an index into the token stream, advances it as tokens are consumed,
and raises a `LambSemanticError` if the stream does not match the expected
structure.

Operator precedence is handled by splitting expression parsing into layered
levels. Comparison operators bind most loosely, then addition and subtraction,
then multiplication and division, then function application, which binds most
tightly. This ensures that `f x + 1` parses as `(f x) + 1` rather than
`f (x + 1)`, and that `2 + 3 * 4` parses as `2 + (3 * 4)`.

---

## Evaluator

The evaluator takes an AST node and an environment and produces a value.
Values are integers, booleans, and closures.

A closure is the value produced when a lambda expression is evaluated. It
packages together the function's parameter name, its body expression, and a
snapshot of the environment at the point of definition. This snapshot is what
makes lexical scoping work.

The environment is a dictionary mapping variable names to values. Each let
binding or function application creates a copy of the current environment
extended with the new binding. The original environment is never mutated,
which ensures that inner scopes can shadow outer bindings without affecting
the outer scope after the inner scope exits.

When a function application is evaluated, the body is evaluated in an
extension of the closure's captured environment — not the caller's
environment. This is the invariant that makes lexical scoping correct.

---

## Closure Semantics in Depth

Consider `make_adder`. When `make_adder 5` is evaluated, the lambda
`fn x => x + n` is evaluated in an environment where `n` is bound to `5`.
This produces a closure that captures that environment. The closure is then
bound to `add5`.

Later, when `add5 10` is evaluated, the closure is applied to `10`. A new
environment is created extending the closure's captured environment, binding
`x` to `10`. The body `x + n` is evaluated in this frame. `x` resolves to
`10` in the new frame. `n` resolves to `5` in the captured frame. The result
is `15`.

If the evaluator had instead extended the caller's environment when applying
the closure, `n` would not necessarily be in scope. Lexical scoping prevents
this class of error by always evaluating a function body in an extension of
its definition environment.

---

## Type Inferencer

The type inferencer implements Hindley-Milner type inference — the algorithm
underlying the type systems of ML, OCaml, and Haskell. It infers the type of
every expression without requiring any type annotations from the programmer.

### Type system

The language has three concrete types: `int`, `bool`, and function types
written `T1 -> T2`. Function types can be nested — a curried two-argument
function has type `int -> int -> int`. Type variables, written `'a`, `'b`,
etc., represent unknown types during inference.

### Pipeline

Type inference runs in three passes over the AST after parsing and before
evaluation.

**Pass 1 — Constraint generation.** The inferencer walks the AST and collects
a list of type equality constraints. Each expression is assigned a type, which
may be a fresh type variable if the type is not yet known. Rules for each
expression form generate constraints:

- Integer literals constrain their type to `int`.
- Boolean literals constrain their type to `bool`.
- Addition and multiplication constrain both operands to `int`.
- Ordering comparisons (`<`, `>`, `<=`, `>=`) constrain both operands to `int` and produce `bool`.
- Equality comparisons constrain both operands to the same type and produce `bool`.
- The condition of an `if` expression is constrained to `bool`.
- Both branches of an `if` expression are constrained to the same type.
- Function application constrains the function to have type `param_type -> return_type`.

**Pass 2 — Unification.** The constraint list is solved. Unification processes
each constraint in order, building a substitution map from type variables to
their resolved types. When a type variable is resolved, the substitution is
applied to all remaining constraints immediately, so that later constraints
benefit from earlier resolutions. If any constraint produces a contradiction —
such as `int = bool` — unification raises a `LambTypeError` before any code
executes.

**Pass 3 — Substitution.** The substitution map is applied to the return type
of the whole expression, replacing all remaining type variables with their
resolved types. The final result is a concrete type for the program.

### Occurs check

Before substituting a type variable `'a` with a type `T`, the inferencer
checks whether `'a` appears anywhere inside `T`. If it does, the substitution
would create an infinite type — for example, `'a = 'a -> int` — which has no
finite representation. This check, called the occurs check, raises a
`LambTypeError` for self-application expressions such as `fn x => x x`.

### Relationship to the evaluator

The type inferencer and the evaluator represent a clean separation between
static and dynamic semantics. The type inferencer reasons about what types
expressions will have. The evaluator computes what values they produce. A
program only reaches the evaluator if it passes type checking.

This separation also explains the treatment of self-application. The untyped
evaluator can execute `fn x => x x` successfully — untyped lambda calculus
permits self-application, and the Y combinator relies on it. The type
inferencer rejects it because `fn x => x x` requires `x` to simultaneously
have type `'a` and type `'a -> 'b`, which the occurs check detects as an
infinite type. Adding the type inferencer makes the language simply-typed,
which intentionally rules out this class of program.

### Type errors caught

The type inferencer catches the following before any evaluation occurs:

- Arithmetic applied to boolean values: `true + 1`
- Ordering comparisons applied to booleans: `true < false`
- Equality comparisons between mismatched types: `1 == true`
- If branches with incompatible types: `if true then 1 else false`
- Non-boolean conditions: `if 1 then 2 else 3`
- Applying a non-function value as a function: `let x = 5 in x 3`
- Passing a wrong-typed argument: `let f = fn x => x + 1 in f true`
- Self-application: `fn x => x x`

---

## Key Concepts Demonstrated

Lexical analysis is demonstrated by the hand-written tokenizer. Recursive
descent parsing is demonstrated by the parser whose structure mirrors the
grammar directly. The environment model is demonstrated by the dictionary
copying strategy used to represent scope. Lexical scoping is demonstrated
by the rule that function application always extends the closure's captured
environment. Closure semantics are demonstrated by the Closure value type.
Beta reduction is demonstrated by function application. Higher-order functions
are demonstrated throughout the example programs. Hindley-Milner type
inference is demonstrated by the constraint generation, unification, and
substitution pipeline. The occurs check is demonstrated by the rejection of
self-application.

---

## Known Limitations and Future Improvements

**Recursion via self-application**

```
let factorial =
  fn self => fn n =>
    if n == 0 then 1 else n * (self self (n - 1))
in factorial factorial 5
```

Evaluates to `120`. The language does not have built-in recursion. Recursion
is instead expressed through self-application — a function receives itself
as an argument and calls itself through that parameter.

Note: self-application in this form is valid at the evaluator level but will
be rejected by the type inferencer. See the Type Inferencer section for the
explanation. 

The planned extension is a letrec keyword that adds the binding to the environment 
before evaluating the value expression, allowing the function to reference itself. 
This requires a straightforward change to the evaluator and a fresh type variable 
approach in the type inferencer.

**Let-polymorphism**

```
let id = fn x => x in if id true then id 5 else id 1 
```

In the current type system, id is assigned a single type at its binding site. The first use id true pins 
'a = bool, which causes id 5 to fail unification. Let-polymorphism generalizes the type at let bindings — 
each use of id gets a fresh instantiation of 'a -> 'a — making the expression well-typed. This is the 
missing piece between the current constraint-based system and full Algorithm W.

**Pattern matching**

```
let result = 5 in
match result with
| 0 => false
| _ => true
```

Evaluates to `true`. In my college course (mentioned below), we implemented pattern matching, but I initially
decided to skip it to simplify the implementation, and add it after. The parser and evaluator would need to support a 
new expression form and pattern binding semantics, but for completeness I will be adding this eventually.

**Better Error Messaging**

Current:

```LambTypeError: Failed to unify types: int <> bool```

Improved:

```
LambTypeError at position 23-27:
  Type mismatch in arithmetic expression
  Expected: int
  Got:      bool
  
  let x = 5 in true + x
                ^^^^
```

---

## Background

This project was built to demonstrate the core concepts from a graduate
compiler construction course (CSCI 742) covering lexical analysis, parsing,
type systems, semantics, and interpreters — originally implemented in Clojure,
rebuilt here in Python.

The language design is influenced by the ML family of languages, with syntax
inspired by OCaml and semantics grounded in the untyped lambda calculus as
described in Essentials of Programming Languages by Friedman and Wand and
Structure and Interpretation of Computer Programs by Abelson and Sussman.
The type inferencer is based on Algorithm W as described in the compiler
construction literature.
