"""
Web search service integrating Tavily API with DuckDuckGo live search fallback.
Synthesizes source-grounded answers with citations (title, URL, snippet, date).
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.core.config import settings
from backend.services.chat_service import ChatService

logger = logging.getLogger(__name__)


class WebSearchService:
    """Executes live web searches and formats grounded answers with citations."""

    @classmethod
    def search_web(cls, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute live web search using Tavily if configured, or DuckDuckGo Search as reliable fallback.
        Returns a list of structured source items.
        """
        results: List[Dict[str, Any]] = []

        # 1. Try Tavily if configured
        if settings.has_tavily:
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=settings.TAVILY_API_KEY)
                tavily_resp = client.search(
                    query=query,
                    max_results=max_results,
                    search_depth="basic"
                )
                for item in tavily_resp.get("results", []):
                    results.append({
                        "title": item.get("title", "Untitled Source"),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "date": item.get("published_date") or datetime.now().strftime("%Y-%m-%d")
                    })
                if results:
                    logger.info("Retrieved %d search results from Tavily.", len(results))
                    return results
            except Exception as e:
                logger.warning("Tavily search attempt failed: %s. Falling back to DuckDuckGo Search.", str(e))

        # 2. Free live search fallback via DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                for item in ddg_results:
                    results.append({
                        "title": item.get("title", "Untitled Web Result"),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", ""),
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
            logger.info("Retrieved %d search results from DuckDuckGo Search.", len(results))
            return results
        except Exception as e:
            logger.error("DuckDuckGo search error: %s", str(e))
            return []

    @classmethod
    def answer_with_search(cls, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Performs web search and synthesizes a grounded response distinguishing
        sourced facts from AI interpretation.
        """
        search_results = cls.search_web(query, max_results=max_results)

        if not search_results:
            return {
                "answer": (
                    "I attempted to search the web for your query, but could not retrieve any live results. "
                    "This could be due to network connectivity or search provider limits. "
                    "Please try refining your search keywords or verify your Tavily API configuration."
                ),
                "sources": [],
                "results_count": 0
            }

        # Build context from web search results
        context_parts = []
        for i, item in enumerate(search_results, 1):
            context_parts.append(
                f"[Source {i}: {item['title']}]\nURL: {item['url']}\nDate: {item.get('date', 'N/A')}\nSnippet: {item['snippet']}"
            )
        context_str = "\n\n---\n\n".join(context_parts)

        # Grounded system prompt
        search_prompt = (
            "You are a helpful research assistant that answers questions using current web search results.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Ground your answer in the provided search results below.\n"
            "2. Clearly distinguish between SOURCED FACTS (explicitly stated in the search results) "
            "and AI INTERPRETATION / REASONING.\n"
            "3. Cite your sources in the text using bracketed titles or numbers (e.g. [Source 1]).\n"
            "4. Provide a clear, concise synthesis.\n\n"
            f"=== WEB SEARCH RESULTS ===\n{context_str}\n=== END SEARCH RESULTS ==="
        )

        answer = ChatService.generate_reply(
            history=[],
            user_message=query,
            system_instruction=search_prompt
        )

        return {
            "answer": answer,
            "sources": search_results,
            "results_count": len(search_results)
        }

