# Unit tests for Case.validate_comment_length in app/core/cases.py.
# The other comment methods (add_comment) require a live DB connection and are
# covered by the integration tests in test_comments.py.

from app.core.cases import Case


def test_validate_comment_valid():
    assert Case.validate_comment_length("This is a valid comment") is True


def test_validate_comment_single_character():
    assert Case.validate_comment_length("A") is True


def test_validate_comment_empty_string():
    assert Case.validate_comment_length("") is False


def test_validate_comment_whitespace_only():
    assert Case.validate_comment_length("   ") is False


def test_validate_comment_tabs_and_newlines():
    assert Case.validate_comment_length("\t\n") is False


def test_validate_comment_none():
    assert Case.validate_comment_length(None) is False


def test_validate_comment_non_string_int():
    assert Case.validate_comment_length(123) is False


def test_validate_comment_non_string_list():
    assert Case.validate_comment_length(["comment"]) is False


def test_validate_comment_strips_whitespace():
    # Surrounding whitespace is stripped before checking, so content is still valid
    assert Case.validate_comment_length("  hello  ") is True
