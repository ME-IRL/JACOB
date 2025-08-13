from typing import List

from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool


class MultiAssistant:
    tools: List[BaseTool]

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.llm = ChatOpenAI(base_url=base_url, api_key=api_key)
        self.tools = []

    def add_tool(self, new_tool) -> None:
        self.tools.append(new_tool)
        self.llm = self.llm.bind_tools(self.tools)

    def chat(self, msg: str, history: List[BaseMessage]) -> str:
        history.append(HumanMessage(msg))
        resp = self.llm.invoke(history)
        history.append(resp)

        while resp.response_metadata["finish_reason"] != "stop":
            if resp.tool_calls:
                history[-1].content = " "  # Server errors when content is empty. (See prompt template)
                for tool in resp.tool_calls:
                    for rtool in self.tools:
                        if rtool.name == tool["name"]:
                            history.append(rtool.invoke(tool))

            resp = self.llm.invoke(history)
            history.append(resp)

        return resp.content


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

    def chat(self, msg: str) -> str:
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
