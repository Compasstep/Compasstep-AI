# app/domains/peer_reputation/schemas.py
from pydantic import BaseModel
from typing import Optional, Any

class PeerReputationRequest(BaseModel):
    postId: int


class ErrorResponse(BaseModel):
    code: str
    message: str
    result: Optional[Any] = None
