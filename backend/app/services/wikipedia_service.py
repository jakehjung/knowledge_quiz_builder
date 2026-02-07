import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WikipediaService:
    BASE_URL = "https://en.wikipedia.org/w/api.php"

    async def search_and_extract(
        self, topic: str, max_chars: int = 8000
    ) -> Optional[str]:
        """
        Search Wikipedia for a topic and extract relevant content for RAG.
        Returns None if Wikipedia is unavailable or topic not found.
        """
        try:
            headers = {
                "User-Agent": "QuizBuilder/1.0 (Educational Quiz Application; contact@example.com)"
            }
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                # First, search for the topic
                search_params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": topic,
                    "format": "json",
                    "srlimit": 3,
                }

                search_response = await client.get(self.BASE_URL, params=search_params)

                if search_response.status_code != 200:
                    logger.warning(
                        f"Wikipedia search failed with status {search_response.status_code}"
                    )
                    return None

                if not search_response.content:
                    logger.warning("Wikipedia returned empty response")
                    return None

                search_data = search_response.json()

                if not search_data.get("query", {}).get("search"):
                    logger.info(f"No Wikipedia results found for: {topic}")
                    return None

                # Get the top result's page ID
                top_result = search_data["query"]["search"][0]
                page_title = top_result["title"]

                # Extract the page content
                extract_params = {
                    "action": "query",
                    "titles": page_title,
                    "prop": "extracts",
                    "explaintext": True,
                    "format": "json",
                    "exlimit": 1,
                }

                extract_response = await client.get(
                    self.BASE_URL, params=extract_params
                )

                if extract_response.status_code != 200:
                    logger.warning(
                        f"Wikipedia extract failed with status {extract_response.status_code}"
                    )
                    return None

                extract_data = extract_response.json()

                pages = extract_data.get("query", {}).get("pages", {})
                if not pages:
                    return None

                # Get the first page's extract
                page = list(pages.values())[0]
                content = page.get("extract", "")

                # Truncate to max_chars
                if len(content) > max_chars:
                    content = content[:max_chars] + "..."

                return content

        except httpx.TimeoutException:
            logger.warning(f"Wikipedia request timed out for: {topic}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Wikipedia request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Wikipedia service error: {e}")
            return None
