# app/coaching/prompts.py

def build_vocal_coaching_prompt(analysis_result: dict) -> str:
    return f"""
당신은 전문 보컬 코치입니다.
입력으로 가사 분석 결과(JSON 형태)가 주어집니다.
각 라인(part)과 2개의 감정(emotions)을 바탕으로,
해당 줄을 어떻게 불러야 하는지 구체적인 보컬 가이드를 제시하세요.

출력 형식(JSON):

[
  {{
    "part": "...",
    "emotions": ["...", "..."],
    "coaching": "..."
  }},
  ...
]

입력:
{analysis_result}
"""
