"""Search API integrations."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import json

from config.settings import config

logger = logging.getLogger(__name__)

class SearchAPI:
    """Search API integrations for web research."""

    def __init__(self):
        self.google_api_key = config.google_api_key
        self.google_cse_id = config.google_cse_id
        self.bing_api_key = config.bing_api_key
        self.perplexity_api_key = config.perplexity_api_key

        # Skip placeholder values
        if self.google_api_key and self.google_api_key.startswith("your_"):
            self.google_api_key = None
        if self.google_cse_id and self.google_cse_id.startswith("your_"):
            self.google_cse_id = None
        if self.bing_api_key and self.bing_api_key.startswith("your_"):
            self.bing_api_key = None
        if self.perplexity_api_key and self.perplexity_api_key.startswith("your_"):
            self.perplexity_api_key = None

    async def search_google(self, query: str, num_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        if not self.google_api_key or not self.google_cse_id:
            logger.warning("Google API credentials not configured")
            return []

        try:
            import aiohttp

            base_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": query,
                "num": min(num_results, 10),  # Google limits to 10 per request
                "start": kwargs.get("start", 1)
            }

            # Add optional parameters
            if "date_restrict" in kwargs:
                params["dateRestrict"] = kwargs["date_restrict"]
            if "site_search" in kwargs:
                params["siteSearch"] = kwargs["site_search"]

            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    results = []
                    if "items" in data:
                        for item in data["items"]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "source": "google",
                                "query": query
                            })

                    return results

        except ImportError:
            logger.warning("aiohttp not available for Google search")
            return []
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

    async def search_bing(self, query: str, num_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search using Bing Search API."""
        if not self.bing_api_key:
            logger.warning("Bing API key not configured")
            return []

        try:
            import aiohttp

            base_url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                "Ocp-Apim-Subscription-Key": self.bing_api_key
            }
            params = {
                "q": query,
                "count": min(num_results, 50),  # Bing allows up to 50
                "responseFilter": "Webpages",
                "setLang": "en-US"
            }

            # Add optional parameters
            if "freshness" in kwargs:
                params["freshness"] = kwargs["freshness"]

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(base_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    results = []
                    if "webPages" in data and "value" in data["webPages"]:
                        for item in data["webPages"]["value"]:
                            results.append({
                                "title": item.get("name", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("snippet", ""),
                                "source": "bing",
                                "query": query
                            })

                    return results

        except ImportError:
            logger.warning("aiohttp not available for Bing search")
            return []
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return []

    async def search_duckduckgo(self, query: str, num_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (no API key required)."""
        try:
            import aiohttp
            from urllib.parse import quote

            # DuckDuckGo doesn't have an official API, so we'll use their HTML interface
            # This is a simplified implementation
            search_url = f"https://duckduckgo.com/html/?q={quote(query)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    response.raise_for_status()
                    html_content = await response.text()

                    # Simple HTML parsing (in production, use BeautifulSoup)
                    results = self._parse_duckduckgo_html(html_content, query, num_results)
                    return results

        except ImportError:
            logger.warning("aiohttp not available for DuckDuckGo search")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    def _parse_duckduckgo_html(self, html: str, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results (simplified implementation)."""
        results = []

        try:
            # This is a very basic implementation
            # In production, you'd want to use proper HTML parsing

            # Look for result patterns in HTML
            import re

            # Find result links and titles
            result_pattern = r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            matches = re.findall(result_pattern, html, re.IGNORECASE)

            for url, title in matches[:num_results]:
                if url and title:
                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "snippet": f"Result from DuckDuckGo search for: {query}",
                        "source": "duckduckgo",
                        "query": query
                    })

        except Exception as e:
            logger.error(f"Error parsing DuckDuckGo results: {e}")

        return results

    async def search_perplexity(self, query: str, num_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search using Perplexity AI."""
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not configured")
            return []

        try:
            import aiohttp

            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }

            # Use the correct Perplexity model for online search
            payload = {
                "model": "sonar",  # Perplexity online search model
                "messages": [
                    {
                        "role": "user",
                        "content": f"Search for recent information about: {query}. Provide {num_results} relevant results with titles, URLs, and brief summaries. Format as numbered list."
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.1
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()

                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # For Perplexity, return the response as a single comprehensive result
                    if content:
                        return [{
                            "title": f"Perplexity Search: {query}",
                            "url": f"https://perplexity.ai/search?q={query.replace(' ', '+')}",
                            "snippet": content[:500] + "..." if len(content) > 500 else content,
                            "content": content,
                            "source": "perplexity",
                            "query": query
                        }]
                    else:
                        return []

        except ImportError:
            logger.warning("aiohttp not available for Perplexity search")
            return []
        except Exception as e:
            logger.error(f"Perplexity search error: {e}")
            return []


    async def search_multiple_sources(
        self,
        query: str,
        sources: List[str] = None,
        num_results: int = 10,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search multiple sources concurrently."""
        if sources is None:
            sources = ["perplexity", "google", "bing", "duckduckgo"]

        # Create search tasks
        tasks = []
        results = {}

        if "perplexity" in sources and self.perplexity_api_key:
            tasks.append(("perplexity", self.search_perplexity(query, num_results, **kwargs)))

        if "google" in sources and self.google_api_key and self.google_cse_id:
            tasks.append(("google", self.search_google(query, num_results, **kwargs)))

        if "bing" in sources and self.bing_api_key:
            tasks.append(("bing", self.search_bing(query, num_results, **kwargs)))

        if "duckduckgo" in sources:
            tasks.append(("duckduckgo", self.search_duckduckgo(query, num_results, **kwargs)))

        # Execute searches concurrently
        if tasks:
            search_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

            for i, (source, _) in enumerate(tasks):
                if isinstance(search_results[i], Exception):
                    logger.error(f"Search failed for {source}: {search_results[i]}")
                    results[source] = []
                else:
                    results[source] = search_results[i]

        return results

    def combine_results(self, search_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combine and deduplicate results from multiple sources."""
        all_results = []
        seen_urls = set()

        # Collect all results
        for source, results in search_results.items():
            for result in results:
                url = result.get("url", "").lower()
                if url and url not in seen_urls:
                    result["search_sources"] = [source]
                    all_results.append(result)
                    seen_urls.add(url)
                elif url in seen_urls:
                    # URL already seen, add source to existing result
                    for existing_result in all_results:
                        if existing_result.get("url", "").lower() == url:
                            if "search_sources" not in existing_result:
                                existing_result["search_sources"] = []
                            existing_result["search_sources"].append(source)
                            break

        # Sort by relevance (simple implementation)
        # In production, you'd want more sophisticated ranking
        all_results.sort(key=lambda x: len(x.get("search_sources", [])), reverse=True)

        return all_results

    async def search_and_combine(
        self,
        query: str,
        sources: List[str] = None,
        num_results: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search multiple sources and combine results."""
        search_results = await self.search_multiple_sources(query, sources, num_results, **kwargs)
        combined_results = self.combine_results(search_results)

        # Limit to requested number of results
        return combined_results[:num_results]

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that API keys are configured."""
        return {
            "perplexity": bool(self.perplexity_api_key),
            "google": bool(self.google_api_key and self.google_cse_id),
            "bing": bool(self.bing_api_key),
            "duckduckgo": True  # No API key required
        }

    def get_available_sources(self) -> List[str]:
        """Get list of available search sources."""
        available = ["duckduckgo"]  # Always available

        if self.perplexity_api_key:
            available.append("perplexity")

        if self.google_api_key and self.google_cse_id:
            available.append("google")

        if self.bing_api_key:
            available.append("bing")

        return available