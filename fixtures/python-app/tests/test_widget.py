from sample_widget import add, classify


def test_add() -> None:
    assert add(2, 2) == 4


def test_classify() -> None:
    assert classify(1) == "pos"
    assert classify(-1) == "neg"
    assert classify(0) == "zero"
