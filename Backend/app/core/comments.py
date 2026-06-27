import uuid 
import asyncpg

MAX_COMMENT_LENGTH = 2000

def validate_comment_length(comment: str) -> bool:
    """
    Returns true if the comment is a non-empty string and does not exceed the max character limit.
    Returns false if it's empty, whitespace or exceeds the limit.
    """

    if not isinstance(comment, str):
        return False
    stripped_comment = comment.strip()
    return 0 < len(stripped_comment) <= MAX_COMMENT_LENGTH

async def get_case_status(connection: asyncpg.Connection, case_id: uuid.UUID) -> str:
    """
    Looks up the case id by its id and returns its curr status.

    Returns:
        'not_found' - no case with this specific id exists
        'closed' - the case is closed and also exists
        'open' - the case is open and also exists
    """

    row = await connection.fetchrow(
        """
        SELECT caseClosed
        FROM "Cases_DB"."Cases"
        WHERE caseId = $1
        """,
        case_id
    )

    if row is None:
        return "not_found"

    return "closed" if row["caseclosed"] else "open"

async def insert_comment(connection: asyncpg.Connection, case_id: uuid.UUID, username: str, comment: str) -> dict:
    """
    Inserts a new comment into the COmments table and returns the created record.
    """

    row = await connection.fetchrow(
        """
        INSERT INTO "Cases_DB"."Comments" (caseid, username, comment)
        VALUES ($1, $2, $3)
        RETURNING commentId, caseid, username, comment, commenttimestamp
        """,
        case_id,
        username,
        comment.strip()
    )

    return {
        "commentId": row["commentid"],
        "caseId": row["caseid"],
        "username": row["username"],
        "comment": row["comment"],
        "timestamp": row["commenttimestamp"].isoformat() if row["commenttimestamp"] else None 
    }