"""
app/integrations/tmdb_client.py
─────────────────────────────────
Async TMDb client with Cloudflare Worker proxy support.
"""

import asyncio
import logging
from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import (
    NotFoundException,
    ServiceUnavailableException,
)

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(20)


class TMDbClient:
    BASE_URL = settings.TMDB_BASE_URL
    IMAGE_BASE = settings.TMDB_IMAGE_BASE

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _build_url(self, path: str) -> str:
        """
        Prevent duplicate /3 prefix when using Cloudflare Worker proxy.
        """

        if self.BASE_URL.endswith("/3") and path.startswith("/3"):
            path = path[2:]

        return path

    async def __aenter__(self) -> "TMDbClient":
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            params={"api_key": settings.TMDB_API_KEY},
            timeout=settings.TMDB_REQUEST_TIMEOUT,
            headers={
                "Accept": "application/json",
                "User-Agent": "CineAI/1.0",
            },
        )

        return self

    async def __aexit__(self, *_) -> None:
        if self._client:
            await self._client.aclose()

    async def _get(
        self,
        path: str,
        params: dict | None = None,
    ) -> dict:
        """
        GET request with retries and proxy-safe URL handling.
        """

        assert self._client, "Use TMDbClient as async context manager"

        retries = 3

        for attempt in range(retries):
            async with _semaphore:
                try:
                    final_path = self._build_url(path)

                    resp = await self._client.get(
                        final_path,
                        params=params or {},
                    )

                    if resp.status_code == 404:
                        raise NotFoundException(
                            f"TMDb resource not found: {final_path}"
                        )

                    if resp.status_code == 429:
                        retry_after = int(
                            resp.headers.get("Retry-After", 1)
                        )

                        await asyncio.sleep(retry_after)
                        continue

                    resp.raise_for_status()

                    return resp.json()

                except httpx.TimeoutException:
                    if attempt == retries - 1:
                        raise ServiceUnavailableException(
                            "TMDb API timed out"
                        )

                    await asyncio.sleep(2**attempt)

                except NotFoundException:
                    raise

                except httpx.HTTPStatusError as exc:
                    if (
                        exc.response.status_code >= 500
                        and attempt < retries - 1
                    ):
                        await asyncio.sleep(2**attempt)
                        continue

                    raise ServiceUnavailableException(
                        f"TMDb HTTP error: {exc}"
                    )

                except httpx.ConnectError as exc:
                    logger.exception("TMDb connection failed")

                    if attempt == retries - 1:
                        raise ServiceUnavailableException(
                            f"TMDb connection failed: {exc}"
                        )

                    await asyncio.sleep(2**attempt)

        raise ServiceUnavailableException(
            "TMDb API unreachable after retries"
        )

    # ──────────────────────────────────────────────────────────────────────
    # Movie endpoints
    # ──────────────────────────────────────────────────────────────────────

    async def get_movie(
        self,
        movie_id: int,
    ) -> dict[str, Any]:
        data = await self._get(
            f"/movie/{movie_id}",
            params={
                "append_to_response": "credits,keywords",
            },
        )

        return self._normalise_movie(data)

    async def get_trending(
        self,
        page: int = 1,
        window: str = "week",
    ) -> dict[str, Any]:

        data = await self._get(
            f"/trending/movie/{window}",
            params={"page": page},
        )

        return {
            "results": [
                self._normalise_movie_card(m)
                for m in data.get("results", [])
            ],
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
        }

    async def discover_movies(
        self,
        params: dict,
    ) -> dict[str, Any]:

        data = await self._get(
            "/discover/movie",
            params=params,
        )

        return {
            "results": [
                self._normalise_movie_card(m)
                for m in data.get("results", [])
            ],
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
        }

    async def search_movies(
        self,
        query: str,
        page: int = 1,
    ) -> dict[str, Any]:

        data = await self._get(
            "/search/movie",
            params={
                "query": query,
                "page": page,
            },
        )

        return {
            "results": [
                self._normalise_movie_card(m)
                for m in data.get("results", [])
            ],
            "total_pages": data.get("total_pages", 1),
        }

    async def get_popular(
        self,
        page: int = 1,
    ) -> dict[str, Any]:

        data = await self._get(
            "/movie/popular",
            params={"page": page},
        )

        return {
            "results": [
                self._normalise_movie_card(m)
                for m in data.get("results", [])
            ],
            "total_pages": data.get("total_pages", 1),
        }

    async def get_top_rated(
        self,
        page: int = 1,
    ) -> dict[str, Any]:

        data = await self._get(
            "/movie/top_rated",
            params={"page": page},
        )

        return {
            "results": [
                self._normalise_movie_card(m)
                for m in data.get("results", [])
            ],
            "total_pages": data.get("total_pages", 1),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Normalisers
    # ──────────────────────────────────────────────────────────────────────

    def _normalise_movie(
        self,
        data: dict,
    ) -> dict[str, Any]:

        credits = data.get("credits", {})
        keywords_data = data.get("keywords", {})

        return {
            "tmdb_id": data["id"],
            "title": data.get("title", ""),
            "original_title": data.get("original_title"),
            "overview": data.get("overview"),
            "tagline": data.get("tagline"),
            "release_date": data.get("release_date") or None,
            "runtime": data.get("runtime"),
            "original_language": data.get("original_language"),
            "status": data.get("status"),
            "vote_average": data.get("vote_average", 0.0),
            "vote_count": data.get("vote_count", 0),
            "popularity": data.get("popularity", 0.0),
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "genres": [
                g["name"]
                for g in data.get("genres", [])
            ],
            "crew": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "job": c["job"],
                }
                for c in credits.get("crew", [])
                if c.get("job")
                in ("Director", "Producer", "Writer")
            ],
            "cast": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "character": c.get("character", ""),
                }
                for c in credits.get("cast", [])[:10]
            ],
            "keywords": [
                k["name"]
                for k in keywords_data.get("keywords", [])
            ],
            "production_companies": [
                c["name"]
                for c in data.get(
                    "production_companies",
                    [],
                )[:3]
            ],
        }

    def _normalise_movie_card(
        self,
        data: dict,
    ) -> dict[str, Any]:

        return {
            "tmdb_id": data["id"],
            "title": data.get("title", ""),
            "overview": data.get("overview"),
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "vote_average": data.get("vote_average", 0.0),
            "vote_count": data.get("vote_count", 0),
            "popularity": data.get("popularity", 0.0),
            "release_date": data.get("release_date"),
            "genres": [],
        }


def get_tmdb_client() -> TMDbClient:
    return TMDbClient()