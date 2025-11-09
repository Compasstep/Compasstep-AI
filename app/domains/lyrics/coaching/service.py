# app/domains/lyrics/coaching/service.py
"""
import os

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .prompts import build_vocal_coaching_prompt

load_dotenv()

AI_MODEL = os.getenv("AI_MODEL")

def generate_vocal_coaching(analysis_result: dict, model=AI_MODEL, temperature=0.7):
    llm = ChatOpenAI(model=model, temperature=temperature)
    prompt = build_vocal_coaching_prompt(analysis_result)
    response = llm.invoke(prompt)
    return response.content
"""
# app/domains/lyrics/coaching/service.py

import os
import json
import re
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .prompts import build_vocal_coaching_prompt

load_dotenv()

AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")  # default (환경에 맞게 설정)
DEFAULT_TEMPERATURE = 0.7

def _extract_json_from_text(text: str) -> str:
    """
    1) 코드블록 제거 (```json ... ``` 또는 ``` ... ```)
    2) 첫 번째 JSON object 또는 array 를 추출 (greedy to last brace so it grabs the object)
    3) 반환된 문자열은 json.loads 가능한 문자열이어야 함.
    """
    if not isinstance(text, str):
        raise ValueError("LLM 응답이 문자열이 아닙니다.")

    # 1) 제거: ```...``` 블록
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)

    # 2) Trim surrounding whitespace
    text = text.strip()

    # 3) Try direct json.loads first
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # 4) Try to find first {...} or [...] block (non-greedy)
    #    Use DOTALL so newlines are included.
    m_obj = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if m_obj:
        candidate = m_obj.group(1)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    m_arr = re.search(r"(\[.*\])", text, flags=re.DOTALL)
    if m_arr:
        candidate = m_arr.group(1)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    # 5) As fallback, try to remove leading non-json garbage until first brace
    first_brace = re.search(r"[\{\[]", text)
    last_brace = re.search(r"[\}\]]\s*$", text)
    if first_brace and last_brace:
        start = first_brace.start()
        end = last_brace.end()
        candidate = text[start:end]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    raise ValueError("LLM 응답에서 JSON을 추출하지 못했습니다.")

def _validate_coaching_list(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(obj, dict):
        raise ValueError("LLM 출력은 최상위 JSON 객체여야 합니다.")
    if "coachingList" not in obj:
        raise ValueError('LLM 출력에 "coachingList" 키가 없습니다.')
    if not isinstance(obj["coachingList"], list):
        raise ValueError('"coachingList"는 리스트여야 합니다.')
    # Basic item validation
    for item in obj["coachingList"]:
        if not isinstance(item, dict):
            raise ValueError("coachingList의 항목은 객체여야 합니다.")
        if "index" not in item or "coaching" not in item:
            raise ValueError('각 항목은 "index"와 "coaching"을 포함해야 합니다.')
        if not isinstance(item["index"], int):
            raise ValueError('"index"는 정수여야 합니다.')
        if not isinstance(item["coaching"], str):
            raise ValueError('"coaching"은 문자열이어야 합니다.')
    return obj["coachingList"]


def generate_vocal_coaching(analysis_indexed: List[Dict[str, Any]], model: str = AI_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> Dict[str, Any]:
    """
    입력: analysis_indexed = [
        {"index": 0, "part": "...", "emotions": ["...","..."]},
        ...]
    반환: {"coachingList": [ {"index":0,"coaching":"..."}, ... ]}
    예외: 파싱 실패 시 ValueError 발생
    """
    if not isinstance(analysis_indexed, list):
        raise ValueError("analysis_indexed는 리스트여야 합니다.")

    # Build prompt (the prompt function will receive the JSON-representation)
    prompt = build_vocal_coaching_prompt(analysis_indexed)

    # LLM 호출
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke(prompt)
    raw = response.content if hasattr(response, "content") else str(response)

    # 안전하게 JSON 추출 / 파싱
    try:
        json_text = _extract_json_from_text(raw)
        parsed = json.loads(json_text)
        coaching_list = _validate_coaching_list(parsed)
        return {"coachingList": coaching_list}
    except Exception as e:
        # 파싱 실패: 호출부에서 예외 처리하도록 ValueError로 전달
        raise ValueError(f"LLM 파싱 실패: {str(e)}")
