"""Good Explorer — FastAPI backend for price comparison."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.comparator import compare_list, compare_prices

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("good-explorer")

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Good Explorer", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SearchRequest(BaseModel):
    query: str
    quantity: str = ""
    platforms: list[str] | None = None


class ListSearchRequest(BaseModel):
    items: list[dict]


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/search")
async def search(req: SearchRequest):
    """Search for a single item across all platforms."""
    result = await compare_prices(
        req.query, req.quantity, req.platforms,
    )
    return result


@app.post("/api/compare-list")
async def search_list(req: ListSearchRequest):
    """Compare prices for a list of items."""
    results = await compare_list(req.items)
    return {"items": results}
