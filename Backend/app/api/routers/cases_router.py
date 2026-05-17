from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.cases import Case

router = APIRouter(
    prefix="/api",
    tags=["Cases"]
)

class CreateCaseRequest(BaseModel):
    CaseName: str | None = None
    CaseCreator: str | None = None

@router.post("/cases")
async def create_case(request: CreateCaseRequest):
    try:
        case = Case(CaseName=request.CaseName, CaseCreator=request.CaseCreator)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    case_id = await case.save()

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "CaseId": case_id
        }
    )
