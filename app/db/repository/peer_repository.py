# app/db/repository/peer_repository.py
import json
from datetime import datetime
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger("peer_reputation_repository")


class PeerReputationRepository:
    """💾 DB 접근 전용 레포지토리"""

    # ------------------------------------------------------------------
    async def get_guest_comments(self, db: AsyncSession, post_id: int) -> List[Dict]:
        """guest_comments 테이블에서 특정 post_id의 모든 댓글 조회"""
        query = text("""
            SELECT id, comment AS comment_text, created_at
            FROM guest_comments
            WHERE post_id = :post_id
        """)
        rows = (await db.execute(query, {"post_id": post_id})).mappings().all()
        comments = [
            {
                "id": r["id"],
                "text": r["comment_text"],
                "created_at": r.get("created_at"),
            }
            for r in rows
        ]
        logger.debug(f"[PeerReputationRepo] {len(comments)} comments fetched for post_id={post_id}")
        return comments

    # ------------------------------------------------------------------
    async def update_post_summary(
        self,
        db: AsyncSession,
        post_id: int,
        share_summary: Dict,
        share_details: Dict,
        keywords: List[str],
    ):
        """posts 테이블에 요약, 세부 감정, 키워드, 수정시각 업데이트"""
        now = datetime.utcnow()

        update_query = text("""
            UPDATE posts
            SET share_summary = :summary,
                share_details = :details,
                keywords = :keywords,
                updated_at = :updated_at
                analyzed = true
            WHERE id = :post_id
        """)
        await db.execute(
            update_query,
            {
                "summary": json.dumps(share_summary),
                "details": json.dumps(share_details),
                "keywords": json.dumps(keywords),
                "updated_at": now,
                "post_id": post_id,
            },
        )
        await db.commit()

        logger.info(f"[PeerReputationRepo] ✅ Updated post_id={post_id} summary")
        return now
