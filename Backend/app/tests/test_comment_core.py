#Here we have unit tests for the comment helper functions in app/core/cases.py
#Only the validate_comment_length function is tested here, since the other functions are more complex and require a database connection to test properly.

from app.core.cases import validate_comment_length

def test_validate_comment_valid():
    assert validate_comment_length("This is a valid comment") is True


def test_validate_comment_single_character():
    assert validate_comment_length("A") is True


def test_validate_comment_empty_string():
    assert validate_comment_length("") is False


def test_validate_comment_whitespace_only():
    assert validate_comment_length("   ") is False


def test_validate_comment_tabs_and_newlines():
    assert validate_comment_length("\t\n") is False


def test_validate_comment_none():
    assert validate_comment_length(None) is False


def test_validate_comment_non_string_int():
    assert validate_comment_length(123) is False


def test_validate_comment_non_string_list():
    assert validate_comment_length(["comment"]) is False


def test_validate_comment_strips_whitespace():
    # Surrounding whitespace is stripped before checking thus content still valid
    assert validate_comment_length("  hello  ") is True