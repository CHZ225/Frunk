from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from flask import jsonify


class CalcError(Exception):
    pass


@dataclass
class Token:
    value: str

    @property
    def is_operator(self) -> bool:
        return self.value in {"+", "-", "*", "/", "u-"}

    @property
    def is_number(self) -> bool:
        return not self.is_operator and self.value not in {"(", ")"}


def tokenize(expr: str) -> List[Token]:
    if not expr or expr.strip() == "":
        raise CalcError("Empty expression")

    tokens: List[Token] = []
    number = ""

    def push_number() -> None:
        nonlocal number
        if number == "":
            return
        tokens.append(Token(number))
        number = ""

    for char in expr:
        if char.isdigit() or char == ".":
            if char == "." and "." in number:
                raise CalcError("Invalid number format")
            if char == "." and number == "":
                number = "0"
            number += char
            continue

        if char.isspace():
            continue

        if char in {"(", ")"}:
            push_number()
            prev = tokens[-1].value if tokens else None
            if char == "(":
                if prev and (Token(prev).is_number or prev == ")"):
                    raise CalcError("Invalid operator sequence")
                tokens.append(Token(char))
                continue

            if not prev or Token(prev).is_operator or prev == "(":
                raise CalcError("Invalid operator sequence")
            tokens.append(Token(char))
            continue

        if char in {"+", "-", "*", "/"}:
            push_number()
            prev = tokens[-1].value if tokens else None
            if char == "-" and (not prev or Token(prev).is_operator or prev == "("):
                tokens.append(Token("u-"))
                continue

            if not prev or Token(prev).is_operator or prev == "(":
                raise CalcError("Invalid operator sequence")

            tokens.append(Token(char))
            continue

        raise CalcError("Invalid character")

    push_number()

    if not tokens:
        raise CalcError("Empty expression")

    last = tokens[-1].value
    if Token(last).is_operator or last == "(":
        raise CalcError("Invalid operator sequence")

    return tokens


def to_postfix(tokens: List[Token]) -> List[Token]:
    output: List[Token] = []
    stack: List[Token] = []
    precedence = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2,
        "u-": 3,
    }

    for token in tokens:
        if token.is_number:
            output.append(token)
            continue

        if token.value == "(":
            stack.append(token)
            continue

        if token.value == ")":
            while stack and stack[-1].value != "(":
                output.append(stack.pop())
            if not stack:
                raise CalcError("Mismatched parentheses")
            stack.pop()
            continue

        while stack:
            top = stack[-1]
            if not top.is_operator:
                break
            should_pop_left = (
                precedence[top.value] >= precedence[token.value] and token.value != "u-"
            )
            should_pop_right = (
                precedence[top.value] > precedence[token.value] and token.value == "u-"
            )
            if should_pop_left or should_pop_right:
                output.append(stack.pop())
            else:
                break

        stack.append(token)

    while stack:
        token = stack.pop()
        if token.value == "(":
            raise CalcError("Mismatched parentheses")
        output.append(token)

    return output


def evaluate_postfix(tokens: List[Token]) -> Decimal:
    stack: List[Decimal] = []

    for token in tokens:
        if token.is_number:
            try:
                stack.append(Decimal(token.value))
            except Exception as exc:
                raise CalcError("Invalid number format") from exc
            continue

        if token.value == "u-":
            if not stack:
                raise CalcError("Invalid expression")
            stack.append(-stack.pop())
            continue

        if len(stack) < 2:
            raise CalcError("Invalid expression")

        right = stack.pop()
        left = stack.pop()

        if token.value == "+":
            stack.append(left + right)
        elif token.value == "-":
            stack.append(left - right)
        elif token.value == "*":
            stack.append(left * right)
        elif token.value == "/":
            if right == 0:
                raise CalcError("Cannot divide by zero")
            stack.append(left / right)
        else:
            raise CalcError("Invalid expression")

    if len(stack) != 1:
        raise CalcError("Invalid expression")

    return stack[0]


def format_result(value: Decimal) -> float | int | str:
    quantized = value.quantize(Decimal("1.000000000000"), rounding=ROUND_HALF_UP)
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", "-0.0"}:
        text = "0"
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def calc_expr(expr: str):
    try:
        tokens = tokenize(expr)
        postfix = to_postfix(tokens)
        result = evaluate_postfix(postfix)
        return jsonify({"ok": True, "result": format_result(result)}), 200
    except CalcError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

