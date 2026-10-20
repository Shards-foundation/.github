"""Package with one function the unit test does not call."""


def covered(value: int) -> int:
    return value + 1


def uncovered(value: int) -> int:
    return value + 2
