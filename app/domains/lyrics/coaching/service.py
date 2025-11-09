# app/coaching/service.py
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
