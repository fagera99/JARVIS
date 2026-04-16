"""
Web search tool for JARVIS.
Uses DuckDuckGo for privacy-preserving web searches.
"""

import json
from typing import Any


def web_search_tool(query: str, max_results: int = 5) -> str:
    """
    Search the web for current information.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        Formatted search results as a string
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        output_parts = [f"🔍 Web Search Results for: '{query}'\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "No description")
            href = r.get("href", "")
            output_parts.append(f"{i}. **{title}**")
            output_parts.append(f"   {body}")
            if href:
                output_parts.append(f"   URL: {href}")
            output_parts.append("")

        return "\n".join(output_parts)

    except ImportError:
        return "Web search is not available. Please install duckduckgo-search."
    except Exception as e:
        return f"Web search failed: {str(e)}"


def web_fetch_tool(url: str, max_chars: int = 3000) -> str:
    """
    Fetch and extract text content from a URL.

    Args:
        url: The URL to fetch
        max_chars: Maximum characters to return

    Returns:
        Extracted text content from the page
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... truncated at {max_chars} characters]"

        return f"📄 Content from {url}:\n\n{text}"

    except ImportError:
        return "Web fetch is not available. Please install requests and beautifulsoup4."
    except Exception as e:
        return f"Failed to fetch URL: {str(e)}"


# Tool definitions for OpenAI function calling
WEB_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current, real-time information. "
            "Use this when you need up-to-date information, news, facts, or anything "
            "that may have changed since your training data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}

WEB_FETCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Fetch and read the content of a specific webpage URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch",
                },
            },
            "required": ["url"],
        },
    },
}
