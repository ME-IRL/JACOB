from datetime import datetime

from langchain_core.tools import tool


@tool(parse_docstring=True)
def get_time() -> str:
    """Get the current time."""
    return datetime.now().astimezone().__str__()
