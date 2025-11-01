from pathlib import Path
import re
from collections import Counter
from typing import List

from konlpy.tag import Okt
import nltk
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer

# ---------------------------------------------------------
# 🧩 초기 세팅, 한국어 영어 통합 불용어 사전 로드
# ---------------------------------------------------------
okt = Okt()
lemmatizer = WordNetLemmatizer()

# NLTK 리소스 (최초 1회만 다운로드 필요)
# uv run python -m nltk.downloader punkt averaged_perceptron_tagger wordnet
# 또는 파이썬 콘솔에서 직접 실행:
# import nltk; nltk.download("punkt"); nltk.download("averaged_perceptron_tagger"); nltk.download("wordnet")

STOPWORDS_PATH = Path(__file__).resolve().parent / "stopwords.txt"
STOPWORDS = set()

if STOPWORDS_PATH.exists():
    with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith("#"):
                STOPWORDS.add(word)

# ---------------------------------------------------------
# 🧹 텍스트 정규화
# ---------------------------------------------------------
def normalize_text(text: str) -> str:
    """URL, 특수문자 제거 및 공백 정규화"""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\s가-힣A-Za-z]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------
# 🇰🇷 한국어 명사 + 🇺🇸 영어 (POS + Lemma) 혼합 키워드 추출
# ---------------------------------------------------------
def extract_keywords_mixed(texts: List[str], top_k: int = 20) -> List[str]:
    tokens = []

    for t in texts:
        t = normalize_text(t)

        # ① 한국어 명사 추출
        ko_nouns = [
            w for w in okt.nouns(t)
            if len(w) > 1 and w not in STOPWORDS
        ]

        # ② 영어 키워드 추출 (품사 + 원형화)
        words = word_tokenize(t)
        tagged = pos_tag(words)
        en_words = [
            lemmatizer.lemmatize(w.lower())
            for (w, pos) in tagged
            if pos.startswith(("N", "J"))  # 명사(N), 형용사(J)만
            and len(w) > 2
            and w.lower() not in STOPWORDS
        ]

        tokens.extend(ko_nouns + en_words)

    freq = Counter(tokens)
    return [k for k, _ in freq.most_common(top_k)]
