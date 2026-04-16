"""Pydantic models for Good Explorer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    """A single item to search for."""

    name: str = Field(..., min_length=1, description="Item name")
    quantity: str = Field(default="", description="Quantity, e.g. '1 kg', '500 ml', '2 packs'")


class SearchRequest(BaseModel):
    """Request to search items across platforms."""

    items: list[SearchItem]
    pincode: str = Field(default="110001", pattern=r"^\d{6}$")


class ProductResult(BaseModel):
    """Price result from a single platform."""

    platform: str
    platform_logo: str = ""
    product_name: str
    price: float
    mrp: float = 0.0
    discount_pct: float = 0.0
    quantity: str = ""
    delivery_time: str = ""
    in_stock: bool = True
    product_url: str = ""
    image_url: str = ""


class ComparisonResult(BaseModel):
    """Comparison results for a single item across platforms."""

    search_term: str
    requested_quantity: str = ""
    cheapest: ProductResult | None = None
    results: list[ProductResult] = []
