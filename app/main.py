"""Good Explorer — FastAPI backend for price comparison."""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.scrapers.price_engine import search_all_platforms, search_list

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
    return await search_all_platforms(req.query, req.quantity)


@app.post("/api/compare-list")
async def compare_list_endpoint(req: ListSearchRequest):
    """Compare prices for a list of items with consolidated summary."""
    results, summary = await search_list(req.items)
    return {"items": results, "summary": summary}
