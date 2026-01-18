"""
title: Giphy Search and Embed Tool
description: Search Giphy for GIFs and display them in the chat
version: 1.0.1
author: elfin8er
author_site: https://github.com/elfin8er/Open_WebUI_Stuff
git_url: https://github.com/elfin8er/Open_WebUI_Stuff.git
requires: aiohttp, fastapi, pydantic
"""

import random
import aiohttp
from typing import Optional, Any, Callable, Awaitable
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

async def emit_embed(
    gif: dict,
    __event_emitter__: Callable[[dict], Awaitable[None]],
) -> None:        
        await __event_emitter__({
            "type": "message",
            "data": {
                "content": f"![test]({gif['images']['original']['url']})\n[via GIPHY]({gif['url']})"
            }
        })

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
        GIF_RATING: str = Field(
            default="g",
            description="Content rating for GIFs (e.g., g, pg, pg-13, r)",
        )
        GIF_LANG: str = Field(
            default="en",
            description="Language for search results",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def search_gifs(self, query: str, __event_emitter__: Callable[[dict], Awaitable[None]]):
        """
        Search for a GIF on Giphy and embed it in the chat.
        :param query: The search term to find a GIF (e.g., 'funny cat').
        :return: A status message indicating if the GIF was found.
        """
        if not self.valves.GIPHY_API_KEY:
            return "ERROR: GIPHY_API_KEY is not set in Valves configuration."
        if not query:
            return "ERROR: No search query provided."
        await emit_status(__event_emitter__, f"Searching Giphy for: {query}")
        url = f"{self.valves.API_BASE_URL}/gifs/search?api_key={self.valves.GIPHY_API_KEY}&q={query}&limit={self.valves.GIF_LIMIT}&offset=0&rating={self.valves.GIF_RATING}&lang={self.valves.GIF_LANG}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 403:
                        return "Error: Invalid API key or API quota exceeded. Please check your Giphy API key and quota."
                    elif response.status != 200:
                        return f"Error: Giphy API returned status {response.status}"
                    
                    search_data = await response.json()
                    if not search_data['data']:
                        return f"ERROR: No GIFs found for query: {query}"
                    gif = search_data['data'][random.randint(0, len(search_data['data']) - 1)]
                    await emit_status(__event_emitter__, f"Displaying gif from query: {query}", done=True)
                    await emit_embed(gif, __event_emitter__)
                    return f"Successfully found and displayed a GIF for '{query}'."
        except Exception as e:
            return f"Error occurred while searching Giphy: {str(e)}"