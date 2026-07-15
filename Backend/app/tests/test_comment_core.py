# Unit tests for Case.validateCommentLength in app/core/cases.py.
# The other comment methods (addComment) require a live DB connection and are
# covered by the integration tests in test_comments.py.

from app.core.cases import Case


def test_validate_comment_valid():
    assert Case.validateCommentLength("This is a valid comment") is True


def test_validate_comment_single_character():
    assert Case.validateCommentLength("A") is True


def test_validate_comment_empty_string():
    assert Case.validateCommentLength("") is False


def test_validate_comment_whitespace_only():
    assert Case.validateCommentLength("   ") is False


def test_validate_comment_tabs_and_newlines():
    assert Case.validateCommentLength("\t\n") is False


def test_validate_comment_none():
    assert Case.validateCommentLength(None) is False


def test_validate_comment_non_string_int():
    assert Case.validateCommentLength(123) is False


def test_validate_comment_non_string_list():
    assert Case.validateCommentLength(["comment"]) is False


def test_validate_comment_strips_whitespace():
    # Surrounding whitespace is stripped before checking, so content is still valid
    assert Case.validateCommentLength("  hello  ") is True
