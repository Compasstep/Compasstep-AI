import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from .prompts import build_prompt
from .tools import TOOLS
from dotenv import load_dotenv

load_dotenv()

AI_MODEL = os.getenv("AI_MODEL")

def build_agent_executor(model: str = AI_MODEL, temperature: float = 0.0) -> AgentExecutor:

    llm = ChatOpenAI(model=model, temperature=temperature)
    prompt = build_prompt()
    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
        max_execution_time=20,
    )