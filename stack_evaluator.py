"""DCOMP320: evaluate infix arithmetic with two custom stacks."""
import argparse
import re
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


class Stack:
    """Last in, first out collection backed by a Python list."""
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("Cannot pop an empty stack")
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            raise IndexError("Cannot peek at an empty stack")
        return self._items[-1]

    def is_empty(self):
        return not self._items

    def __len__(self):
        return len(self._items)


NUMBER = re.compile(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")
PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "u+": 3, "u-": 3}


def tokenize(expression):
    """Scan every character; unsupported input cannot be silently skipped."""
    tokens = []
    i = 0
    while i < len(expression):
        if expression[i].isspace():
            i += 1
            continue
        match = NUMBER.match(expression, i)
        if match:
            tokens.append(match.group())
            i = match.end()
        elif expression[i] in "+-*/()":
            tokens.append(expression[i])
            i += 1
        else:
            raise ValueError(f"Invalid character at position {i + 1}")
    return tokens


def apply_operator(values, operators):
    """Pop right operand first to preserve subtraction and division order."""
    operator = operators.pop()
    if operator in ("u+", "u-"):
        if len(values) < 1:
            raise ValueError("Missing operand")
        value = values.pop()
        values.push(-value if operator == "u-" else value)
        return
    if len(values) < 2:
        raise ValueError("Missing operand")
    right, left = values.pop(), values.pop()
    if operator == "+":
        result = left + right
    elif operator == "-":
        result = left - right
    elif operator == "*":
        result = left * right
    else:
        if right == 0:
            raise ValueError("Division by zero")
        result = left / right
    values.push(result)


def evaluate_expression(expression):
    """Return a Fraction using the two-stack infix evaluation algorithm."""
    tokens = tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    values, operators = Stack(), Stack()
    expect_operand = True
    for token in tokens:
        if NUMBER.fullmatch(token):
            if not expect_operand:
                raise ValueError("Missing operator")
            values.push(Fraction(token))
            expect_operand = False
        elif token == "(":
            if not expect_operand:
                raise ValueError("Missing operator before parenthesis")
            operators.push(token)
        elif token == ")":
            if expect_operand:
                raise ValueError("Missing operand before closing parenthesis")
            while not operators.is_empty() and operators.peek() != "(":
                apply_operator(values, operators)
            if operators.is_empty():
                raise ValueError("Unmatched closing parenthesis")
            operators.pop()
            expect_operand = False
        else:
            if expect_operand:
                if token not in ("+", "-"):
                    raise ValueError("Missing operand")
                operators.push("u" + token)
                continue
            while (not operators.is_empty() and operators.peek() != "("
                   and PRECEDENCE[operators.peek()] >= PRECEDENCE[token]):
                apply_operator(values, operators)
            operators.push(token)
            expect_operand = True
        # Unary signs apply immediately after their operand is complete.
        while (not expect_operand and not operators.is_empty()
               and operators.peek() in ("u+", "u-")):
            apply_operator(values, operators)
    if expect_operand:
        raise ValueError("Expression ends without an operand")
    while not operators.is_empty():
        if operators.peek() == "(":
            raise ValueError("Unmatched opening parenthesis")
        apply_operator(values, operators)
    if len(values) != 1:
        raise ValueError("Invalid expression")
    return values.pop()


def format_result(value):
    """Display integers exactly; round other results to 12 significant digits."""
    if value.denominator == 1:
        return str(value.numerator)
    with localcontext() as context:
        context.prec = 12
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def process_file(input_path, output_path):
    """Keep blank lines and hyphen separators; replace expression lines."""
    if Path(input_path).resolve() == Path(output_path).resolve():
        raise ValueError("Input and output paths must be different")
    lines = Path(input_path).read_text(encoding="utf-8").splitlines()
    output, count, errors = [], 0, 0
    for line in lines:
        stripped = line.strip()
        if not stripped or re.fullmatch(r"-{3,}", stripped):
            output.append(line)
            continue
        count += 1
        try:
            output.append(format_result(evaluate_expression(stripped)))
        except ValueError as error:
            output.append(f"Error: {error}")
            errors += 1
    Path(output_path).write_text("\n".join(output) + ("\n" if lines else ""), encoding="utf-8")
    return count, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="input.txt")
    parser.add_argument("output", nargs="?", default="output.txt")
    arguments = parser.parse_args()
    try:
        count, errors = process_file(arguments.input, arguments.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Processed {count} expressions; {errors} errors. Results: {arguments.output}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
