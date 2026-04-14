## Extended Backus–Naur form

The lambda calculus language described in the README.md is defined below.

```text
<expr> ::= let <identifier> = <expr> in <expr>
       | fn <identifier> => <expr>
       | if <expr> then <expr> else <expr>
       | <expr> <expr>                  
       | <expr> op <expr>                
       | ( <expr> )
       | <identifier>
       | <integer>
       | true
       | false

<op>   ::= + | - | * | / | == | < | >

<identifier> ::= [a-zA-Z][a-zA-Z0-9_]*

<integer> ::= [0-9]+
```
