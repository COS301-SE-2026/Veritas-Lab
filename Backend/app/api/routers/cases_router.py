from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.cases import Case
from app.auth.auth import verifyJWT

router = APIRouter(
    prefix="/api",
    tags=["Cases"]
)

class CreateCaseRequest(BaseModel):
    title: str | None = None
    description: str | None = None

@router.post("/createCase")
async def create_case(request: CreateCaseRequest, authorization: str | None = Header(default=None)):
    try:
        payload = verifyJWT(authorization)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    if payload.get("role") == "USER":
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "message": "User unauthorized"
            }
        )

    try:
        case = Case(CaseName=request.title, CaseCreator=payload["username"], CaseDescription=request.description)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    case_id = await case.create()

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "CaseId": case_id
        }
    )
