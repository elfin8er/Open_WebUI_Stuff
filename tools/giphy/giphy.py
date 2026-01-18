"""
title: Giphy Search and Embed Tool
description: Search Giphy for GIFs and display them in the chat
version: 1.1.0
author: elfin8er, nahoj
author_site: https://github.com/elfin8er/Open_WebUI_Stuff
git_url: https://github.com/elfin8er/Open_WebUI_Stuff.git
requires: aiohttp, pydantic
"""

from typing import Optional, Any, Callable, Awaitable, Literal

import random
import aiohttp
from pydantic import BaseModel, Field


async def emit_status(
    event_emitter: Optional[Callable[[Any], Awaitable[None]]],
    description: str,
    done: bool = False,
) -> None:
    """Helper to emit status events"""
    if event_emitter:
        await event_emitter(
            {"type": "status", "data": {"description": description, "done": done}}
        )


class Tools:
    class Valves(BaseModel):
        GIPHY_API_KEY: str = Field(
            default="",
            description="API key for Giphy",
        )
        API_BASE_URL: str = Field(
            default="https://api.giphy.com/v1",
            description="Base URL for Giphy API",
        )
        GIF_LIMIT: int = Field(
            default=6,
            description="Number of GIFs to retrieve per search",
        )

    class UserValves(BaseModel):
        GIF_LANG: str = Field(
            default="en",
            description="Language for search results",
        )
        GIF_RATING: Literal["g", "pg", "pg-13", "r"] = Field(
            default="g",
            description="Content rating for GIFs",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def search_gifs(
        self,
        query: str,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        __user__: Optional[dict] = None,
    ):
        """
        Search for a GIF on Giphy.
        :param query: The search term to find a GIF (e.g., 'funny cat').
        :return: A markdown embed string to embed the gif in the chat.
        """
        user_valves = self.UserValves.model_validate(__user__.get("valves", {}))

        if not self.valves.GIPHY_API_KEY:
            return "ERROR: GIPHY_API_KEY is not set in Valves configuration."
        if not query:
            return "ERROR: No search query provided."
        await emit_status(__event_emitter__, f"Searching Giphy for: {query}")
        url = (
            f"{self.valves.API_BASE_URL}/gifs/search"
            f"?api_key={self.valves.GIPHY_API_KEY}"
            f"&q={query}"
            f"&limit={self.valves.GIF_LIMIT}"
            f"&offset=0"
            f"&rating={user_valves.GIF_RATING}"
            f"&lang={user_valves.GIF_LANG}"
        )
        # await emit_status(__event_emitter__, f"Giphy URL: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 403:
                        return "Error: Invalid API key or API quota exceeded. Please check your Giphy API key and quota."
                    elif response.status != 200:
                        return f"Error: Giphy API returned status {response.status}"

                    search_data = await response.json()
                    # await emit_status(__event_emitter__, f"Got response: {search_data}")
                    if not search_data["data"]:
                        return f"ERROR: No GIFs found for query: {query}"
                    gif = search_data['data'][random.randint(0, len(search_data['data']) - 1)]
                    await emit_status(__event_emitter__, f"Displaying gif from query: {query}")
                    await emit_status(__event_emitter__, gif['url'], done=True)
                    return f"![from giphy]({gif['images']['original']['url']}) [via GIPHY]({gif['url']})"
        except Exception as e:
            return f"Error occurred while searching Giphy: {str(e)}"
