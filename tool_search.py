from typing import Dict, List

from ddgs import DDGS
from langchain_core.tools import tool

ddgsearch = DDGS()


def search_internet(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    try:
        results = ddgsearch.text(query, max_results=max_results)
        # Filter out irrelevant results
        filtered_results = [result for result in results if "body" in result]
        return filtered_results
    except Exception as e:
        print(f"Error searching internet: {e}")
        return []


@tool(parse_docstring=True)
def get_search_results(query: str, max_results: int = 5) -> str:
    """Perform a search on DuckDuckGo and return formatted results.

    This function uses the DDGS (DuckDuckGo Search) library to perform
    internet searches and returns the results in a structured string format.

    Args:
        query (str): The search query to perform on DuckDuckGo.
        max_results (int, optional): The maximum number of search results to return.
            Defaults to 5, capped to 20.

    Returns:
        str: A formatted string containing search results. Each result includes:
            - Title: The title of the search result
            - URL: The URL of the search result
            - Snippet: A brief description/snippet from the search result

        The format is:
        ```
        Title: <title>
        URL: <url>
        Snippet: <snippet>

        Title: <title>
        URL: <url>
        Snippet: <snippet>
        ```
        (with blank lines between results)

    Raises:
        Exception: If there's an error during the search operation, it will be
            caught and handled, returning an empty string.

    Example:
        >>> get_search_results("Python programming")
        'Title: Python Programming - Wikipedia
        URL: https://en.wikipedia.org/wiki/Python_(programming_language)
        Snippet: Python is an interpreted, high-level, general-purpose programming language...

        Title: Real Python
        URL: https://realpython.com/
        Snippet: Learn Python programming with free online courses, tutorials, and books...
        '
    """
    max_results = min(max_results, 20)
    search_results = search_internet(query, max_results)
    output = ""
    for result in search_results:
        output += f"Title: {result['title']}\n"
        output += f"URL: {result['href']}\n"
        output += f"Snippet: {result['body']}\n\n"
    return output
