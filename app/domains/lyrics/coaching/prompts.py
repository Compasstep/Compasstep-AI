# app/domains/lyrics/coaching/prompts.py

def build_vocal_coaching_prompt(analysis_result: dict) -> str:
    return f"""
당신은 보컬 코치입니다.
입력으로 아래 구조의 리스트가 JSON 형태로 제공됩니다.

[
  {{ "index": 0, "part": "가사 한 줄", "emotions": ["감정1", "감정2"] }},
  {{ "index": 1, "part": "가사 한 줄", "emotions": ["감정1", "감정2"] }}
]

각 index에 대해 part, emotions를 참고하여 **보컬 코칭 한 줄**만 생성하세요.
코칭은 감정만 나열하지 말고, 반드시 아래 요소 중 2가지 이상을 포함해 구체적으로 지시하세요.
- 발성(두성/가성/흉성), 호흡 길이, 음 끝 처리, 톤 밝기/어두움, 다이내믹(크레센도/디크레센도), 딕션, 비브라토, 감정 실린 포인트
- 한 줄이지만 밀도 높게, "어느 단어를", "어떻게 불러야 하는지"를 반드시 포함
- 예) “*바라보면*에서 숨을 살짝 끊고, *보면*에 흉성으로 힘을 실어 슬픔을 눌러 표현하세요.”

⚠️ 출력 규칙
- 출력은 **반드시 1개의 JSON 객체**
- 최상위 키는 **"coachingList"**
- 배열 안은 **index, coaching만**
- part, emotions는 출력 금지
- 설명, 코드블록, 말, 마크다운 금지
- JSON 외에 어떤 문자도 금지

✅ 출력 예시 (이 형식만 허용):

{{
  "coachingList": [
    {{ "index": 0, "coaching": "코칭 멘트 1" }},
    {{ "index": 1, "coaching": "코칭 멘트 2" }}
  ]
}}

입력:
{analysis_result}
"""
