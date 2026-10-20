from sample_lowcov import covered


def test_covered() -> None:
    assert covered(1) == 2
