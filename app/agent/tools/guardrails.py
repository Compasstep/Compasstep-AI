from langchain_core.tools import tool

CUSTOM_MESSAGES = {
    "self-harm": "❗위험 신호가 보여요. 안전이 가장 중요합니다. 가까운 분께 즉시 도움을 요청해 주세요.",
    "pii": "❗개인정보(전화번호/주민번호/정확한 위치) 공유는 제한돼요.",
    "sexual": "❗부적절한 성적 요청은 지원하지 않습니다.",
    "hate": "❗혐오 표현은 사용할 수 없어요.",
    "unrelated": "❗이 질문은 음악 레퍼런스와 관련이 없어요. 음악 관련 질문을 해주세요!",
}

@tool("moderation_tool", return_direct=True)
def moderation_tool(category: str) -> dict:
    """
    This tool is called when the user input violates safety rules or is irrelevant to the music assistant's purpose.
    The input must be one of the categories below:

    - "self-harm": Mentions of suicide, self-harm, wanting to die, etc.
    - "pii": Sharing personal information (phone numbers, social security numbers, exact addresses, etc.)
    - "sexual": Explicit sexual content or pornographic requests
    - "hate": Abusive, insulting, or hateful expressions
    - "unrelated": Questions that are NOT about music or creative references.
        Note: Music-related queries include anything about songs, artists, albums, lyrics, moods, emotions,
        genres, instruments, composition, arrangement, production, performance, and recommendations.
        Only non-music topics (e.g., math, cooking, politics, weather, general chit-chat, etc.) should be classified here.

    The tool returns a safe, user-friendly guidance message corresponding to the category.
    """
    return {
        "message": CUSTOM_MESSAGES.get(category, "규칙 위반이 감지되었습니다."),
        "is_guardrailed": True,  # ← 키 통일: ed 붙이기
    }
