from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.auth.auth import verifyJWT
from app.core.env import ENVLoader
from app.core.comments import validate_comment_length, get_case_status, insert_comment
import asyncpg
from uuid import UUID

env = ENVLoader()

DB_USER = env.getRequiredEnv("DB_USER")
DB_PASSWORD = env.getRequiredEnv("DB_PASSWORD")
DB_HOST = env.getRequiredEnv("DB_HOST")
DB_PORT = env.getRequiredIntEnv("DB_PORT")
DB_NAME = env.getRequiredEnv("DB_NAME")

router = APIRouter(
    prefix="/api",
    tags=["comments"]
)

class CreateCommentRequest(BaseModel):
    #None is allowed so that FastAPI does not throw a validation error if the field is missing. The validation will be done in the endpoint function.
    case_id:  str | None = None
    comment: str | None = None

@router.post("/cases/comments", status_code=201)
async def create_comment(request: CreateCommentRequest, 
    authorization: str | None = Header(default=None)):

    #First step is to authenticate the user
    try:
        payload = verifyJWT(authorization)
    except Exception as e:
        return JSONResponse(status_code=401, 
                            content={"status":"error", "message":str(e)}
        )

    role = payload.get("role")
    username = payload.get("username")

    #Second step is validate the case_id and UUID format
    if not request.case_id:
        return JSONResponse(status_code=400, 
                            content={"status":"error", "message":"case_id is needed."}
        )

    try:
        case_id = UUID(request.case_id)
    except ValueError:
        return JSONResponse(status_code=400, 
                            content={"status":"error", 
                            "message":"Invalid case_id format. Must be a valid UUID"}
        )

    #Third step is to validate the comment text before we even touch the DB
    if not request.comment or not validate_comment_length(request.comment):
        return JSONResponse(status_code=400, 
                            content={"status":"error", 
                            "message":"Invalid comment. Must be a non-empty string and not exceed 2000 characters"}
        )

    connection = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

    try:
        # Fourth sstep is to check whether the case exists and if it is open or closed
        case_status = await get_case_status(connection, case_id)

        if case_status == "not_found":
            return JSONResponse(status_code=404, 
                                content={"status":"error", 
                                "message":"Case not found"}
            )

        # Fifth step. Here a comment can be made while gthe case is ongoing by the investigator.
            #And a User can only make a comment on the case when the case has been closed.

        if case_status != "closed" and role == "USER":
            return JSONResponse(status_code=403, 
                content={"status":"error", 
                    "message":"Users may only comment on closed cases"
                }
            )

        if case_status != "open" and role == "INVESTIGATOR":
            return JSONResponse(status_code=403,
                content={"status":"error",
                    "message":"Investigators may only comment on open cases"
                }
            )

        #Sixth step: Make the comment.
        new_comment = await insert_comment(connection, case_id, username, request.comment)

        return JSONResponse(
            status_code=201,
            content={"status": "success", "comment": new_comment}
        )

    finally:
        await connection.close()