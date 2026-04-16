# Good Explorer 🛒

Compare grocery & household prices across India's top e-commerce platforms.

Search across **Amazon**, **Flipkart**, **BigBasket**, **Blinkit**, **Zepto**, and **JioMart** — find the cheapest option with delivery timelines.

## Quick Start

```bash
cd good-explorer
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn goodexplorer.app:app --reload
```

Open http://localhost:8000 in your browser.

## Features

- 🔍 Search and compare prices across 6 Indian platforms
- 🛒 Smart Cart — finds cheapest combination across platforms
- 📊 Sortable comparison table
- 🌙 Dark mode toggle
- 📱 Mobile responsive
- 💰 Indian Rupee (₹) formatting
- ⚡ Bulk search (one item per line)
- 🚀 "Buy All" opens product pages in new tabs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Frontend dashboard |
| POST | `/api/search` | Compare items across all platforms |
| POST | `/api/search-single` | Search a single item |
| GET | `/api/platforms` | List supported platforms |
| POST | `/api/cart/optimize` | Optimize cart across platforms |

## Tech Stack

- Python 3.11+ / FastAPI / Pydantic v2
- Single-page HTML/CSS/JS frontend (no Node.js)
- httpx for async HTTP
- Demo mode with realistic Indian grocery prices (INR)

## Platforms

| Platform | Delivery | Price Range |
|----------|----------|-------------|
| Amazon | Tomorrow | Mid-range |
| Flipkart | 2-3 days | Competitive |
| BigBasket | 2-4 hours | Often cheapest |
| Blinkit | 10-15 min | Slight premium |
| Zepto | 10 min | Slight premium |
| JioMart | 1-2 days | Often cheapest |

## Note

Prices shown are **demo/simulated data** for demonstration purposes. Each scraper has a fallback mock mode that generates realistic prices when real scraping is unavailable.
