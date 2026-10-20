"""Tiny package used to exercise the org Python CI workflow."""


def add(left: int, right: int) -> int:
    return left + right


def classify(value: int) -> str:
    if value > 0:
        return "pos"
    if value < 0:
        return "neg"
    return "zero"
