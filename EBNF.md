## Extended Backus–Naur Form

The lambda calculus language described in README.md is defined below.

```text
<start>     ::= <expr> eof

<expr>      ::= fn <identifier> => <expr>
             | let rec <identifier> = <expr> in <expr>
             | let <identifier> = <expr> in <expr>
             | if <expr> then <expr> else <expr>
             | <comp_expr>

<comp_expr> ::= <add_expr> [ ( == | < | <= | > | >= ) <add_expr> ]?

<add_expr>  ::= <mul_expr> [ ( + | - ) <mul_expr> ]*

<mul_expr>  ::= <app_expr> [ ( * | / ) <app_expr> ]*

<app_expr>  ::= <atom> <atom>*

<atom>      ::= <identifier>
             | <integer>
             | true | false
             | ( <expr> )

<identifier> ::= [a-zA-Z][a-zA-Z0-9_-]*

<integer>    ::= (-)?[0-9]+
```

### Operator precedence

Operators bind in the following order, tightest first:

1. Function application — `f x`
2. Multiplication and division — `*` `/`
3. Addition and subtraction — `+` `-`
4. Comparison — `==` `<` `<=` `>` `>=`

Parentheses override precedence in the usual way.

### Notes

Function application is left-associative. `f x y` parses as `(f x) y`,
which is the correct behavior for curried multi-argument functions.

Comparison operators do not chain. `a < b < c` is not valid syntax.

The arrow `=>` in lambda abstractions binds greedily to the right.
`fn x => fn y => x + y` parses as `fn x => (fn y => (x + y))`.