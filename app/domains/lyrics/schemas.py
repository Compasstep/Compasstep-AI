# app/domains/lyrics/schemas.py
from pydantic import BaseModel
from typing import Optional, Any

class LyricsAnalyzeRequest(BaseModel):
    lyricsId: int


class ApiResponse(BaseModel):
    code: str
    message: str
    result: Optional[Any] = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    result: Optional[Any] = None
