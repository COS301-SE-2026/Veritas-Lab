#Here we have unit tests for app/core/comments.py
#Only the validate_comment_text function is tested here, since the other functions are more complex and require a database connection to test properly.

from app.core.comments import validate_comment_text, MAX_COMMENT_LENGTH

def test_validate_comment_valid():
    assert validate_comment_text("This is a valid comment") is True


def test_validate_comment_single_character():
    assert validate_comment_text("A") is True


def test_validate_comment_empty_string():
    assert validate_comment_text("") is False


def test_validate_comment_whitespace_only():
    assert validate_comment_text("   ") is False


def test_validate_comment_tabs_and_newlines():
    assert validate_comment_text("\t\n") is False


def test_validate_comment_at_max_length():
    comment = "A" * MAX_COMMENT_LENGTH
    assert validate_comment_text(comment) is True


def test_validate_comment_exceeds_max_length():
    comment = "A" * (MAX_COMMENT_LENGTH + 1)
    assert validate_comment_text(comment) is False

def test_validate_comment_none():
    assert validate_comment_text(None) is False


def test_validate_comment_non_string_int():
    assert validate_comment_text(123) is False


def test_validate_comment_non_string_list():
    assert validate_comment_text(["comment"]) is False


def test_validate_comment_strips_before_length_check():
    # A comment with only surrounding whitespace should be rejected
    padded = "  " + "A" * MAX_COMMENT_LENGTH + "  "
    # The stripped length equals MAX_COMMENT_LENGTH, so it should still pass
    assert validate_comment_text(padded) is True