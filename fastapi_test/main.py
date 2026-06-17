from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional


class Item(BaseModel):
    id: str
    value: str

class NamedHTTPException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, detail: Optional[str] = None):
        if not detail:
            detail = HTTPStatus(status_code).description
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(NamedHTTPException):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

app = FastAPI()


_403 = {
    status.HTTP_403_FORBIDDEN: {
        "content": {
            "application/json": {
                "examples": {
                    "missing_api_key": {
                        "summary": "Missing API key",
                        "value": {"detail": "Not authenticated"},
                    },
                    "invalid_api_key": {
                        "summary": "Invalid or revoked API key",
                        "value": {"detail": "Invalid api key"},
                    },
                    "ip_not_allowed": {
                        "summary": "IP address not allowed",
                        "value": {"detail": "Forbidden: IP address not allowed"},
                    },
                    "quota_exceeded": {
                        "summary": "Usage quota exceeded",
                        "value": {"detail": "Monthly request limit exceeded: 1000 / 1000 requests."},
                    },
                }
            }
        },
    },
}

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses=_403 | {
        404: {"description": "Item not found", "content": {
            "application/json": {
                "example": {"detail": "not found hello"}
            }
        },},
        422: {"description": "Validation error - invalid item_id format"},
    },
)
async def read_item(item_id: str):
    if item_id != "foo":
        raise  NotFoundException("not found hello")
    return {"id": "foo", "value": "there goes my hero"}
