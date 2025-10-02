from pydantic import BaseModel

class DiscoveryRequest(BaseModel):
    user_id: int
    query: str

# 응답 스키마 정의
class AnswerResult(BaseModel):
    answer: str

class ApiResponse(BaseModel):
    code: str
    message: str
    result: AnswerResult | None = None