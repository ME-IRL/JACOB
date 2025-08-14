import logging
from datetime import datetime
from typing import List, Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

logger = logging.getLogger(__name__)


def get_time_raw() -> str:
    return datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

class MultiAssistant:
    """Multi-user assistant for handling AI conversations with tool integration."""

    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[SecretStr] = None
    ):
        """Initialize the multi-assistant with OpenAI configuration.

        Args:
            base_url: Optional base URL for OpenAI API
            api_key: Optional API key for OpenAI
        """
        self.llm = ChatOpenAI(base_url=base_url, api_key=api_key)
        self.tools: List[BaseTool] = []

    def add_tool(self, new_tool: BaseTool) -> None:
        """Add a tool to the assistant's toolkit.

        Args:
            new_tool: Tool to add
        """
        self.tools.append(new_tool)
        self.llm = self.llm.bind_tools(self.tools)
        logger.info(f"Added tool: {new_tool.name}")

    def chat(self, msg: str, history: List[BaseMessage]) -> str:
        """Handle a chat conversation with tool integration.

        Args:
            msg: User message
            history: Conversation history

        Returns:
            AI response
        """
        try:
            history.append(HumanMessage(f"<time>{get_time_raw()}</time> {msg}"))
            resp = self.llm.invoke(history)
            history.append(resp)

            while resp.response_metadata["finish_reason"] != "stop":
                if resp.tool_calls:
                    history[-1].content = " "  # Server errors when content is empty

                    for tool_call in resp.tool_calls:
                        tool_found = False
                        for rtool in self.tools:
                            if rtool.name == tool_call["name"]:
                                tool_result = rtool.invoke(tool_call)
                                history.append(tool_result)
                                tool_found = True
                                logger.info(f"Executed tool: {rtool.name}({tool_call['args']})")
                                break
                        if not tool_found:
                            logger.warning(f"Tool not found: {tool_call['name']}")

                resp = self.llm.invoke(history)
                history.append(resp)

            return resp.content

        except Exception as e:
            logger.error(f"Error in chat processing: {e}", exc_info=True)
            raise


@tool(parse_docstring=True)
def get_time() -> str:
    """Get the current time in the local timezone.

    This tool returns the current date and time formatted as a string,
    including timezone information.

    Returns:
        str: Formatted current date and time with timezone
    """
    try:
        current_time = datetime.now().astimezone()
        result = current_time.__str__()
        logger.info(f"Get time tool executed, returned: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in get_time tool: {e}", exc_info=True)
        raise
