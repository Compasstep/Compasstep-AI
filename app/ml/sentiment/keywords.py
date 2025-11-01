# ---------------------------------------------------------------------------
# 🧩 한국어 + 영어 혼합 키워드 추출기 (stopwords.txt + nltk 기반)
# ---------------------------------------------------------------------------
from pathlib import Path
import re
from collections import Counter
from konlpy.tag import Okt
from typing import List

# -------------------------------
# 🧱 기본 세팅
# -------------------------------
okt = Okt()

# -------------------------------
# 📘 한국어 영어 통합 불용어 (stopwords.txt에서 로드)
# -------------------------------
STOPWORDS_PATH = Path(__file__).resolve().parent / "stopwords.txt"
STOPWORDS = set()
if STOPWORDS_PATH.exists():
    with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith("#"):
                STOPWORDS.add(word)

# -------------------------------
# 🧩 텍스트 정규화
# -------------------------------
def normalize_text(text: str) -> str:
    """URL, 특수문자 제거 및 공백 정규화"""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\s가-힣A-Za-z]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------------
# 🧠 키워드 추출 (한국어 + 영어 혼합)
# -------------------------------
def extract_keywords_mixed(texts: List[str], top_k: int = 20) -> List[str]:
    """
    한국어 명사 + 영어 단어 혼합 키워드 추출기
    - 한국어만 있을 때 → 전부 한국어로
    - 영어만 있을 때 → 전부 영어로
    - 혼용일 때 → 빈도 기반 비율로 자연스럽게 섞임
    """
    tokens = []

    for t in texts:
        t = normalize_text(t)

        # ① 한국어 명사 추출
        ko_nouns = [
            w for w in okt.nouns(t)
            if len(w) > 1 and w not in STOPWORDS
        ]

        # ② 영어 단어 추출
        en_words = [
            w.lower()
            for w in t.split()
            if w.isalpha()
            and w.lower() not in STOPWORDS
            and len(w) > 2
        ]

        tokens.extend(ko_nouns + en_words)

    freq = Counter(tokens)
    if not freq:
        return []

    return [k for k, _ in freq.most_common(top_k)]
