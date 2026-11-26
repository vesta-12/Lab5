"""Temporary assertion failure for the required GREEN -> RED -> GREEN demo."""


def test_intentional_ci_failure():
    assert False, "Intentional CI failure for GREEN -> RED -> GREEN evidence"
