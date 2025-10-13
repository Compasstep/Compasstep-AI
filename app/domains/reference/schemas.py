from typing import Optional, List
from pydantic import BaseModel

class DiscoveryRequest(BaseModel):
    user_id: int
    query: str

# 단일 트랙 비디오 응답 스키마
class TrackVideo(BaseModel):
    videoId: str
    title: str
    channelName: str
    thumbnailUrl: str
    youtubeUrl: str

class ApiResponse(BaseModel):
    code: str
    message: str
    # 원하는 형태대로 result에 객체가 직접 들어가도록 변경
    result: Optional[List[TrackVideo]] = None
