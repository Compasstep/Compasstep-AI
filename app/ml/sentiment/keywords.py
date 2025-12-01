# app/ml/sentiment/keywords.py
from pathlib import Path
import re
from collections import Counter
from typing import List

from konlpy.tag import Okt
import simplemma

# ---------------------------------------------------------
# 초기 세팅, 한국어 영어 통합 불용어 사전 로드
# ---------------------------------------------------------
okt = Okt()

STOPWORDS_PATH = Path(__file__).resolve().parent / "stopwords.txt"
STOPWORDS = set()

if STOPWORDS_PATH.exists():
    with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith("#"):
                STOPWORDS.add(word)

# ---------------------------------------------------------
# 텍스트 정규화
# ---------------------------------------------------------
def normalize_text(text: str) -> str:
    """URL, 특수문자 제거 및 공백 정규화"""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\s가-힣A-Za-z]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------
# 🇰🇷 한국어 명사 + 🇺🇸 영어 (Lemma) 혼합 키워드 추출
# ---------------------------------------------------------
JOSA = [
    "은", "는", "이", "가", "을", "를", "도", "만",
    "와", "과", "로", "으로", "에", "에서", "에게",
    "처럼", "까지", "부터", "조차", "라도"
]

def strip_josa(word: str) -> str:
    for j in JOSA:
        if word.endswith(j) and len(word) > len(j):
            return word[:-len(j)]
    return word

def extract_keywords_mixed(texts: List[str], top_k: int = 20) -> List[str]:
    tokens = []

    for t in texts:
        t = normalize_text(t)

        # ① 한국어 명사 추출
        ko_nouns = [
            strip_josa(w)
            for w in okt.nouns(t)
            if len(w) > 1 and w not in STOPWORDS
        ]
        # ① 한국어 형용사 추출
        ko_adjs = [
            w
            for (w, pos) in okt.pos(t)
            if pos == "Adjective" and len(w) > 1 and w not in STOPWORDS
        ]

        ko_tokens = ko_nouns + ko_adjs

        # ② 영어 단어 정규식 추출
        en_raw = re.findall(r"[A-Za-z]+", t)

        # ③ 영어 단어 lemmatize + 소문자 + stopword 제거
        en_words = [
            simplemma.lemmatize(w.lower(), "en")
            for w in en_raw
            if len(w) > 2 and w.lower() not in STOPWORDS
        ]

        tokens.extend(ko_tokens + en_words)

    freq = Counter(tokens)
    return [k for k, _ in freq.most_common(top_k)]
