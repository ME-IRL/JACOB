import os
from typing import List

from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime

from signalbot import Command, Context, SignalBot

from tools import get_time

API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_URL = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

SIGNAL_SRV = os.environ.get("SIGNAL_SERVICE", "")
SIGNAL_NUM = os.environ.get("PHONE_NUMBER", "")

SYSTEM_PROMPT = "You are a Signal bot named J.A.C.O.B. , short for \"Just Another Cool Online Bot\". Limit your replies to fewer than 500 words. Be flirty."

class GetTime(BaseModel):
    """Get the current time."""

    timezone: str = Field(..., description="The timezone")

    def run(self) -> str:
        return datetime.now()


class Assistant:
    message: List[BaseMessage]
    tools: List[BaseTool]

    def __init__(self, base_url: str | None = None, api_key: str | None = None, system: str | None = None):
        self.message = []
        if system is not None:
            self.message.append(SystemMessage(system))

        self.llm = ChatOpenAI(base_url=base_url, api_key=api_key)
        self.tools = []

    def add_tool(self, new_tool) -> None:
        self.tools.append(new_tool)
        self.llm = self.llm.bind_tools(self.tools)

    def chat(self, msg: str):
        self.message.append(HumanMessage(msg))
        resp = self.llm.invoke(self.message)
        self.message.append(resp)

        while resp.response_metadata["finish_reason"] != "stop":
            if resp.tool_calls:
                self.message[-1].content = " "  # Server errors when content is empty. (See prompt template)
                for tool in resp.tool_calls:
                    for rtool in self.tools:
                        if rtool.name == tool["name"]:
                            self.message.append(rtool.invoke(tool))

            resp = self.llm.invoke(self.message)
            self.message.append(resp)

        return resp.content

    def chat_print(self, msg: str):
        print(f"User: {msg}")
        print(f"Assistant: {self.chat(msg)}")


ai = Assistant(API_URL, API_KEY, SYSTEM_PROMPT)
ai.add_tool(get_time)
# ai.chat_print("What time is it right now?")


class AICommand(Command):
    def __init__(self, ai: Assistant):
        super().__init__()
        self.ai = ai

    async def handle(self, c: Context):
        command = c.message.text

        await c.start_typing()
        resp = self.ai.chat(command)
        await c.stop_typing()
        await c.send(resp)

        # if command == "ping":
        #     await c.send("pong")
        #     return

bot = SignalBot({
    "signal_service": SIGNAL_SRV,
    "phone_number": SIGNAL_NUM,
    "storage": {
        "type": "sqlite",
        "sqlite_db": "signal.db"
    }
})
bot.register(AICommand(ai))
bot.start()