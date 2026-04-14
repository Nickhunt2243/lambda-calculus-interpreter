# Lambda Calculus Interpreter

A small interpreter for a minimal functional language grounded in the untyped
lambda calculus. Built to demonstrate core programming language implementation
concepts: lexical analysis, recursive descent parsing, environment-based
evaluation, and closure semantics.

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

---

## Example Programs

**Basic arithmetic and let bindings**

Bind two values with let and add them. The result is their sum. Let bindings
are not variable assignments — they are expressions that introduce a name
into scope for the duration of their body.

**Curried addition**

Define an add function that takes x and returns a function that takes y and
returns x + y. Apply it to two arguments in sequence. The result is their
sum. This demonstrates that multi-argument functions are just functions
returning functions — currying is not syntactic sugar here, it is the
actual evaluation model.

**Closures capturing outer scope**

Define a make_adder function that takes a number n and returns a function
that adds n to its argument. Call make_adder 5 to produce an add5 function,
then apply add5 to 10. The result is 15.

The key here is that the inner function closes over n from the outer scope.
When make_adder 5 returns, the value 5 is captured inside the returned
closure. Later calls to add5 can still access n even though make_adder has
already finished executing. This is closure semantics in action.

**Conditionals**

Define an abs function using an if-then-else expression to return the
absolute value of its argument. Apply it to a negative number. Conditionals
are expressions, not statements — both branches must be present and both
must produce values of compatible types.

**Recursion via self-application**

The language does not have built-in recursion. Recursion is instead expressed
through self-application: a function receives itself as an argument and calls
itself through that parameter. A factorial function written this way takes
self and n, checks if n is zero, and otherwise multiplies n by the result
of calling self self on n minus 1. This pattern is the basis of the Y
combinator and demonstrates that recursion is not a primitive concept — it
can be derived from the core calculus.

---

## Architecture

The interpreter is a classic three-stage pipeline. Source text enters as a
raw string. The lexer consumes it and produces a flat stream of typed tokens.
The parser consumes the token stream and produces an abstract syntax tree.
The evaluator consumes the AST alongside an environment and produces a value.

Each stage has a clearly defined input and output type. Errors are caught
and reported at the stage where they occur: the lexer reports unrecognized
characters, the parser reports malformed syntax, and the evaluator reports
unbound variables and type mismatches.

---

## Lexer

The lexer performs lexical analysis — converting raw source text into a
sequence of meaningful units called tokens. It works character by character,
recognizing integer literals, boolean keywords, identifiers, reserved words,
operators, arrows, equals signs, and parentheses.

Token types include numbers, booleans, identifiers, keywords such as fn,
let, in, if, then, and else, binary operators, the lambda arrow, the equals
sign used in let bindings, parentheses, and an end-of-input marker.

Whitespace is consumed and discarded between tokens. Identifiers are
distinguished from keywords by checking whether the recognized word appears
in the reserved word set. The lexer is hand-written without regular
expression libraries, scanning the source character by character in a single
pass.

---

## Parser

The parser performs syntactic analysis — consuming the token stream and
constructing an abstract syntax tree that represents the grammatical
structure of the program.

The parser is implemented as a recursive descent parser. Each grammatical
rule in the language corresponds directly to a parsing function. The parser
maintains a pointer into the token stream, advances it as tokens are
consumed, and raises an error if the stream does not match the expected
structure. This one-to-one correspondence between grammar rules and parsing
functions makes the structure easy to follow and extend.

AST node types represent each form in the language: numeric literals,
boolean literals, variable references, binary operations, conditionals,
lambda abstractions, function applications, and let bindings. Each node
carries exactly the information needed to evaluate it.

Operator precedence is handled by splitting expression parsing into multiple
levels. Comparison operators bind most loosely, then addition and
subtraction, then multiplication and division, then function application,
which binds most tightly. This layered approach ensures that expressions
parse according to standard mathematical convention without requiring an
explicit precedence table or a more complex parsing algorithm.

---

## Evaluator

The evaluator performs semantic analysis — taking an AST node and an
environment and producing a value.

Values in the language are integers, booleans, and closures. A closure is
the value produced when a lambda expression is evaluated. It packages
together the function's parameter name, its body expression, and a snapshot
of the environment that was in scope at the point of definition. This
snapshot is what makes lexical scoping work.

The environment is a mapping from variable names to values, implemented as
a linked chain of frames. Each let binding or function application creates
a new frame that extends its parent. Variable lookup walks up the chain
until the binding is found. If the chain is exhausted without finding the
name, the variable is unbound and an error is raised. This linked structure
means that inner scopes can shadow outer bindings without destroying them.

When a lambda expression is evaluated, no computation happens yet. The
evaluator simply wraps the parameter, body, and current environment into
a closure value and returns it. Computation is deferred until the closure
is applied to an argument.

When a function application is evaluated, the evaluator first evaluates
the function expression to obtain a closure, then evaluates the argument
expression to obtain a value. It then creates a new environment frame that
extends the closure's captured environment — not the caller's environment —
binding the parameter to the argument value. The body is then evaluated in
this new environment.

The distinction between extending the closure's captured environment versus
the caller's environment is the entire meaning of lexical scoping. It
ensures that a function always resolves free variables according to where
it was defined, not where it was called.

---

## Closure Semantics in Depth

Closures are the central idea of the project and the concept that makes
higher-order functions work correctly.

Consider make_adder. When make_adder 5 is evaluated, the lambda
fn x => x + n is evaluated in an environment where n is bound to 5. This
produces a closure that captures that environment. The closure is then bound
to add5.

Later, when add5 10 is evaluated, the closure is applied to 10. A new
environment frame is created extending the closure's captured environment,
binding x to 10. The body x + n is evaluated in this frame. x resolves to
10 in the new frame. n resolves to 5 in the captured frame. The result is 15.

If the evaluator had instead extended the caller's environment when applying
the closure, n would not necessarily be in scope and evaluation would fail
or produce wrong results depending on what n meant at the call site. Lexical
scoping prevents this class of error entirely by always evaluating a function
body in an extension of its definition environment.

---

## Key Concepts Demonstrated

The project covers the major topics from a compiler construction curriculum.
Lexical analysis is demonstrated by the hand-written tokenizer that classifies
source characters without regular expression libraries. Recursive descent
parsing is demonstrated by the parser whose structure mirrors the grammar
directly. The environment model is demonstrated by the linked frame chain
used to represent scope. Lexical scoping is demonstrated by the rule that
function application extends the closure's captured environment rather than
the caller's. Closure semantics are demonstrated by the closure value type
that packages a function body with its definition environment. Beta reduction
is demonstrated by function application. Higher-order functions are
demonstrated throughout the example programs, including functions that
return functions and functions that accept functions as arguments.

---

## Background

This project was built to demonstrate the core concepts from a graduate
compiler construction course covering lexical analysis, parsing, type
systems, semantics, and interpreters — originally implemented in Clojure,
rebuilt here in Python.

The language design is influenced by the ML family of languages, with syntax
inspired by OCaml and semantics grounded in the untyped lambda calculus as
described in Essentials of Programming Languages by Friedman and Wand and
Structure and Interpretation of Computer Programs by Abelson and Sussman.
