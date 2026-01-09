"""
title: Giphy Search and Embed Tool
description: Search Giphy for GIFs and display them in the chat
version: 1.0.0
author: elfin8er
author_site: https://github.com/elfin8er/Open_WebUI_Stuff
git_url: https://github.com/elfin8er/Open_WebUI_Stuff.git
requires: aiohttp, fastapi, pydantic
"""

import random
import aiohttp
from typing import Optional, Any, Callable, Awaitable
from fastapi.responses import HTMLResponse
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
) -> HTMLResponse:
        """Helper to emit embed events for displaying gifs"""

        iframe_html = f'''
            <div>
                <iframe src="{gif["embed_url"]}" 
                        width="300" 
                        height="300" 
                        frameBorder="0" 
                        class="giphy-embed" 
                        allowFullScreen>
                </iframe>
                <p style="margin: 0;"><a href="{gif["url"]}">via GIPHY</a></p>
            </div>
        '''.strip()
        return HTMLResponse(content=iframe_html, headers={"content-disposition": "inline"})

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

    def __init__(self):
        self.valves = self.Valves()

    async def search_gifs(self, query, __event_emitter__):
        """Search for gifs with a given query using Giphy API and include gif in response
        Args:
            query (str): The term used to search for GIFs on Giphy.
        """
        if not self.valves.GIPHY_API_KEY:
            return "ERROR: GIPHY_API_KEY is not set in Valves configuration."
        if not query:
            return "ERROR: No search query provided."
        await emit_status(__event_emitter__, f"Searching Giphy for: {query}")
        url = f"{self.valves.API_BASE_URL}/gifs/search?api_key={self.valves.GIPHY_API_KEY}&q={query}&limit=6&offset=0&rating=g&lang=en"
        
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
                    return await emit_embed(gif)
        except Exception as e:
            return f"Error occurred while searching Giphy: {str(e)}"
        

# import asyncio
# test = asyncio.run(Tools().search_gifs("funny cat"))
# print(test)