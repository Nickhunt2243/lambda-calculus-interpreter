from __future__ import annotations

from interpreter.datatypes import (
    BooleanLiteral,
    IntegerLiteral,
    Identifier,
    Token,
    LParen,
    RParen,
    Keyword,
    Arrow,
    BooleanOperations,
    EqualSign,
    AdditiveOperations,
    MultiplicativeOperations
)
from interpreter.exceptions import LambSyntaxError
from interpreter.predicates import is_white_space, is_let_rec, is_left_paren, is_keyword, is_operation, is_equal, \
    is_arrow


def validate_keyword(raw_string: str, start_idx: int, keyword: str):

    # Validate when the keyword is at the end of file
    if start_idx + len(keyword) + 1 >= len(raw_string) >= start_idx + len(keyword):
        return raw_string[start_idx:start_idx + len(keyword)] == keyword, start_idx + len(keyword)
    # Keyword is in the middle of file, so we check
    if start_idx + len(keyword) + 1 < len(raw_string) and is_white_space(raw_string[start_idx + len(keyword)]):
        return raw_string[start_idx:start_idx + len(keyword)] == keyword, start_idx + len(keyword) + 1

    return False, len(raw_string)


def validate_symbol(raw_string: str, start_idx: int, symbol: str):
    # Validate when the keyword is at the end of file
    if start_idx + len(symbol) <= len(raw_string):
        return raw_string[start_idx:start_idx + len(symbol)] == symbol, start_idx + len(symbol)

    return False, len(raw_string)


def expecting_numeric(current_token: Token | None):
    return (
            current_token is None or
            is_keyword(current_token) or
            is_operation(current_token) or
            is_equal(current_token) or
            is_arrow(current_token) or
            is_left_paren(current_token)
    )


def tokenize(raw_string: str):
    tokens: list[Token] = []
    idx = 0
    max_idx = len(raw_string)
    while idx < max_idx:
        while idx < max_idx and is_white_space(raw_string[idx]):
            idx += 1

        c = raw_string[idx]
        if c == "(":
            tokens.append(LParen())
            idx += 1
            continue
        elif c == ")":
            tokens.append(RParen())
            idx += 1
            continue
        elif c == "f":
            valid_fn, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="fn")
            if valid_fn:
                tokens.append(Keyword.FN)
                idx = next_idx
                continue
            valid_false, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="false")
            if valid_false:
                tokens.append(BooleanLiteral(False))
                idx = next_idx
                continue
        elif c == "=":
            valid_arrow, next_idx = validate_symbol(raw_string=raw_string, start_idx=idx, symbol="=>")
            if valid_arrow:
                tokens.append(Arrow())
                idx = next_idx
                continue
            valid_equality, next_idx = validate_symbol(raw_string=raw_string, start_idx=idx, symbol="==")
            if valid_equality:
                tokens.append(BooleanOperations.EQUALITY)
                idx = next_idx
                continue

            # Must be equal sign.
            tokens.append(EqualSign())
            idx += 1
            continue
        elif c == "<":
            valid_less_than, next_idx = validate_symbol(raw_string=raw_string, start_idx=idx, symbol="<=")
            if valid_less_than:
                tokens.append(BooleanOperations.LESS_THAN_EQUAL_TO)
                idx = next_idx
                continue

            # Must be Less than
            tokens.append(BooleanOperations.LESS_THAN)
            idx += 1
            continue
        elif c == ">":
            valid_greater_than, next_idx = validate_symbol(raw_string=raw_string, start_idx=idx, symbol=">=")
            if valid_greater_than:
                tokens.append(BooleanOperations.GREATER_THAN_EQUAL_TO)
                idx = next_idx
                continue

            # Must be Greater than
            tokens.append(BooleanOperations.GREATER_THAN)
            idx += 1
            continue
        elif c == "l":
            valid_letrec, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="letrec")
            if valid_letrec:
                tokens.append(Keyword.LETREC)
                idx = next_idx
                continue
            valid_let, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="let")
            if valid_let:
                tokens.append(Keyword.LET)
                idx = next_idx
                continue
        elif c == "e":
            valid_else, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="else")
            if valid_else:
                tokens.append(Keyword.ELSE)
                idx = next_idx
                continue
        elif c == "t":
            valid_then, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="then")
            if valid_then:
                tokens.append(Keyword.THEN)
                idx = next_idx
                continue
            valid_true, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="true")
            if valid_true:
                tokens.append(BooleanLiteral(True))
                idx = next_idx
                continue
        elif c == "i":
            valid_if, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="if")
            if valid_if:
                tokens.append(Keyword.IF)
                idx = next_idx
                continue
            valid_in, next_idx = validate_keyword(raw_string=raw_string, start_idx=idx, keyword="in")
            if valid_in:
                tokens.append(Keyword.IN)
                idx = next_idx
                continue
        elif "0" <= c <= "9":
            idx += 1
            total_number = c
            while idx < max_idx and "0" <= raw_string[idx] <= "9":
                total_number += raw_string[idx]
                idx += 1
            tokens.append(IntegerLiteral(int(total_number)))
            continue
        elif c == "+":
            tokens.append(AdditiveOperations.ADD)
            idx += 1
            continue
        elif c == "-":
            if expecting_numeric(tokens[-1] if len(tokens) else None):
                idx += 1
                total_number = f"-{raw_string[idx]}"
                idx += 1
                while idx < max_idx and "0" <= raw_string[idx] <= "9":
                    total_number += raw_string[idx]
                    idx += 1
                tokens.append(IntegerLiteral(int(total_number)))
                continue
            else:
                tokens.append(AdditiveOperations.SUB)
                idx += 1
                continue
        elif c == "*":
            tokens.append(MultiplicativeOperations.MUL)
            idx += 1
            continue
        elif c == "/":
            tokens.append(MultiplicativeOperations.DIV)
            idx += 1
            continue

        if c.isalpha():
            ident = c
            idx += 1
            while idx < max_idx and (raw_string[idx].isalnum() or raw_string[idx] in '_-'):
                ident += raw_string[idx]
                idx += 1
            tokens.append(Identifier(name=ident))
        else:
            raise LambSyntaxError(f"Unexpected character: {c}, at: {idx}.")

    return tokens