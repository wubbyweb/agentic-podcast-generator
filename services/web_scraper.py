"""Web scraping utilities."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
import re

from config.settings import config

logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraping utilities for research purposes."""

    def __init__(self):
        self.session = None
        self.user_agent = config.user_agent
        self.request_delay = config.request_delay
        self.max_concurrent = config.max_concurrent_requests

    async def __aenter__(self):
        """Async context manager entry."""
        import aiohttp
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def scrape_url(self, url: str, extract_type: str = "text") -> Dict[str, Any]:
        """Scrape content from a URL."""
        if not self.session:
            raise RuntimeError("WebScraper must be used as async context manager")

        try:
            logger.info(f"Scraping URL: {url}")

            # Add delay to be respectful to servers
            await asyncio.sleep(self.request_delay)

            async with self.session.get(url) as response:
                response.raise_for_status()

                if extract_type == "text":
                    content = await response.text()
                    return self._extract_text_content(content, url)
                elif extract_type == "links":
                    content = await response.text()
                    return self._extract_links(content, url)
                elif extract_type == "metadata":
                    content = await response.text()
                    return self._extract_metadata(content, url, response.headers)
                else:
                    content = await response.text()
                    return {
                        "url": url,
                        "content": content,
                        "content_type": response.headers.get("content-type", ""),
                        "status_code": response.status
                    }

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False
            }

    def _extract_text_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract readable text content from HTML."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()

            # Extract meta description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()

            # Extract main content
            # Try common content selectors
            content_selectors = [
                'main',
                '[role="main"]',
                '.content',
                '.post-content',
                '.entry-content',
                'article',
                '.article-content'
            ]

            main_content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem.get_text(separator=' ', strip=True)
                    break

            # Fallback to body text if no main content found
            if not main_content:
                body = soup.find('body')
                if body:
                    main_content = body.get_text(separator=' ', strip=True)

            # Clean up whitespace
            main_content = re.sub(r'\s+', ' ', main_content).strip()

            return {
                "url": url,
                "title": title,
                "description": description,
                "content": main_content,
                "word_count": len(main_content.split()),
                "success": True
            }

        except ImportError:
            logger.warning("BeautifulSoup not available, returning raw content")
            return {
                "url": url,
                "content": html_content,
                "success": True,
                "note": "BeautifulSoup not available for parsing"
            }
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False
            }

    def _extract_links(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """Extract links from HTML content."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')
            links = []

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.get_text().strip()

                # Convert relative URLs to absolute
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)

                links.append({
                    "url": href,
                    "text": text,
                    "title": a_tag.get('title', '')
                })

            return {
                "url": base_url,
                "links": links,
                "link_count": len(links),
                "success": True
            }

        except ImportError:
            logger.warning("BeautifulSoup not available for link extraction")
            return {
                "url": base_url,
                "links": [],
                "success": True,
                "note": "BeautifulSoup not available for parsing"
            }
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return {
                "url": base_url,
                "error": str(e),
                "success": False
            }

    def _extract_metadata(self, html_content: str, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from HTML and headers."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')
            metadata = {
                "url": url,
                "headers": dict(headers),
                "meta_tags": {},
                "open_graph": {},
                "twitter_cards": {}
            }

            # Extract meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content = meta.get('content')
                if name and content:
                    metadata["meta_tags"][name] = content

                    # Categorize Open Graph tags
                    if name.startswith('og:'):
                        metadata["open_graph"][name[3:]] = content

                    # Categorize Twitter Card tags
                    if name.startswith('twitter:'):
                        metadata["twitter_cards"][name[8:]] = content

            # Extract additional metadata
            metadata.update({
                "title": soup.find('title').get_text().strip() if soup.find('title') else "",
                "language": soup.find('html').get('lang') if soup.find('html') else "",
                "success": True
            })

            return metadata

        except ImportError:
            logger.warning("BeautifulSoup not available for metadata extraction")
            return {
                "url": url,
                "headers": dict(headers),
                "success": True,
                "note": "BeautifulSoup not available for parsing"
            }
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False
            }

    async def scrape_multiple_urls(self, urls: List[str], extract_type: str = "text") -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently."""
        if not self.session:
            raise RuntimeError("WebScraper must be used as async context manager")

        # Create tasks for concurrent scraping
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_url(url, extract_type)

        for url in urls:
            task = asyncio.create_task(scrape_with_semaphore(url))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": urls[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append(result)

        return processed_results

    def is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def clean_url(self, url: str) -> str:
        """Clean and normalize a URL."""
        if not url:
            return ""

        # Remove common tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', '_ga', '_gl'
        ]

        try:
            parsed = urlparse(url)
            query_params = []
            if parsed.query:
                from urllib.parse import parse_qs, urlencode
                params = parse_qs(parsed.query)
                for key in tracking_params:
                    params.pop(key, None)
                if params:
                    query_params = [urlencode(params, doseq=True)]

            # Reconstruct URL
            cleaned = parsed._replace(query='&'.join(query_params) if query_params else '')
            return cleaned.geturl()
        except Exception:
            return url