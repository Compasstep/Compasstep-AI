import boto3
import httpx
from botocore.client import Config
from fastapi import HTTPException
from app.core.constants import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET,
    AWS_S3_REGION,
)

class S3Service:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=AWS_S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = AWS_S3_BUCKET

    def generate_presigned_url(self, object_key: str, expires: int = 600):
        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_key
                },
                ExpiresIn=expires,
            )
            return url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Presigned URL 생성 실패: {e}")

    async def get_lyrics_from_s3(self, object_key: str) -> str:
        url = self.generate_presigned_url(object_key)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url)

                if r.status_code != 200:
                    raise HTTPException(r.status_code, f"S3 다운로드 오류: {r.text[:200]}")

                return r.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3에서 파일 읽기 실패: {e}")
