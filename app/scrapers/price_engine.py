"""Unified price engine using a curated price database.

Provides price comparison across Indian e-commerce platforms
with strict matching logic, category browsing, autosuggest,
and consolidated summary support.
"""

from __future__ import annotations

import logging
import re

from .base import ProductResult

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category definitions with emoji icons
# ---------------------------------------------------------------------------
CATEGORIES = {
    "fruits": {"icon": "🍎", "label": "Fruits"},
    "vegetables": {"icon": "🥬", "label": "Vegetables"},
    "dairy": {"icon": "🥛", "label": "Dairy & Eggs"},
    "staples": {"icon": "🌾", "label": "Staples & Grains"},
    "cooking": {"icon": "🫒", "label": "Cooking Essentials"},
    "snacks": {"icon": "🍪", "label": "Snacks & Namkeen"},
    "beverages": {"icon": "☕", "label": "Beverages"},
    "personal_care": {"icon": "🧴", "label": "Personal Care"},
    "cleaning": {"icon": "🧹", "label": "Cleaning & Household"},
    "baby_care": {"icon": "👶", "label": "Baby Care"},
    "frozen": {"icon": "🧊", "label": "Frozen & Ready to Eat"},
    "pet_care": {"icon": "🐾", "label": "Pet Care"},
}

# Quantity suggestions per category
CATEGORY_QUANTITIES = {
    "fruits": ["250g", "500g", "1kg", "2kg", "5kg"],
    "vegetables": ["250g", "500g", "1kg", "2kg", "5kg"],
    "dairy": ["200ml", "500ml", "1L", "2L"],
    "staples": ["500g", "1kg", "2kg", "5kg", "10kg"],
    "cooking": ["100ml", "200ml", "500ml", "1L", "5L"],
    "snacks": ["50g", "100g", "200g", "500g"],
    "beverages": ["200ml", "500ml", "1L", "2L"],
    "personal_care": ["50ml", "100ml", "200ml", "500ml"],
    "cleaning": ["500ml", "1L", "2L", "5kg"],
    "baby_care": ["1 pack", "2 packs", "3 packs"],
    "frozen": ["250g", "500g", "1kg"],
    "pet_care": ["400g", "1kg", "3kg", "10kg"],
}

# ---------------------------------------------------------------------------
# Curated grocery price database — realistic Indian 2025 prices
# Each entry: key -> list of {name, prices, category}
# ---------------------------------------------------------------------------
PRICE_DB = {
    # ── Fruits ──────────────────────────────────────────────────────────
    "apple": [
        {"name": "Shimla Apple 1kg", "category": "fruits", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 175, "Blinkit": 180, "Zepto": 178}},
        {"name": "Kinnaur Apple Premium 1kg", "category": "fruits", "prices": {"Amazon": 280, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
        {"name": "Kashmiri Apple 1kg", "category": "fruits", "prices": {"Amazon": 320, "Flipkart": 309, "BigBasket": 295, "Blinkit": 305, "Zepto": 299}},
    ],
    "banana": [
        {"name": "Robusta Banana (1 Dozen)", "category": "fruits", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 40, "Blinkit": 42, "Zepto": 41}},
        {"name": "Elaichi Banana 500g", "category": "fruits", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Red Banana (4 pcs)", "category": "fruits", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
    ],
    "papaya": [
        {"name": "Fresh Papaya 1kg", "category": "fruits", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
        {"name": "Semi-Ripe Papaya 1pc (~800g)", "category": "fruits", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
        {"name": "Red Lady Papaya 1kg", "category": "fruits", "prices": {"BigBasket": 65, "Blinkit": 68, "Zepto": 66}},
    ],
    "mango": [
        {"name": "Alphonso Mango (Hapus) 1kg", "category": "fruits", "prices": {"Amazon": 699, "Flipkart": 679, "BigBasket": 649, "Blinkit": 669, "Zepto": 659}},
        {"name": "Kesar Mango 1kg", "category": "fruits", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 369, "Blinkit": 379, "Zepto": 375}},
        {"name": "Totapuri Mango 1kg", "category": "fruits", "prices": {"BigBasket": 89, "Blinkit": 95, "Zepto": 92}},
    ],
    "orange": [
        {"name": "Nagpur Orange 1kg", "category": "fruits", "prices": {"Amazon": 129, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Imported Malta Orange 1kg", "category": "fruits", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Kinnow Orange 1kg", "category": "fruits", "prices": {"BigBasket": 79, "Blinkit": 85, "Zepto": 82}},
    ],
    "grapes": [
        {"name": "Green Seedless Grapes 500g", "category": "fruits", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 85, "Blinkit": 89, "Zepto": 87}},
        {"name": "Black Grapes 500g", "category": "fruits", "prices": {"BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "Red Globe Grapes 500g", "category": "fruits", "prices": {"BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
    ],
    "watermelon": [
        {"name": "Watermelon 1pc (~2-3kg)", "category": "fruits", "prices": {"BigBasket": 59, "Blinkit": 55, "Zepto": 57}},
        {"name": "Watermelon Seedless 1pc (~3kg)", "category": "fruits", "prices": {"BigBasket": 89, "Blinkit": 95, "Zepto": 92}},
        {"name": "Mini Watermelon 1pc (~1.5kg)", "category": "fruits", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
    ],
    "pomegranate": [
        {"name": "Pomegranate (Anar) 500g", "category": "fruits", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 125, "Blinkit": 130, "Zepto": 128}},
        {"name": "Bhagwa Pomegranate 1kg", "category": "fruits", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 219, "Blinkit": 229, "Zepto": 225}},
        {"name": "Pomegranate Arils 200g", "category": "fruits", "prices": {"BigBasket": 99, "Blinkit": 105, "Zepto": 102}},
    ],
    "guava": [
        {"name": "Fresh Guava (Amrood) 500g", "category": "fruits", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
        {"name": "Thai Guava 500g", "category": "fruits", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
        {"name": "Pink Guava 500g", "category": "fruits", "prices": {"BigBasket": 49, "Blinkit": 52, "Zepto": 50}},
    ],
    "kiwi": [
        {"name": "Zespri Green Kiwi (3 pcs)", "category": "fruits", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 155, "Blinkit": 162, "Zepto": 158}},
        {"name": "Golden Kiwi (3 pcs)", "category": "fruits", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 225, "Blinkit": 232, "Zepto": 228}},
        {"name": "Indian Kiwi 500g", "category": "fruits", "prices": {"BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "pineapple": [
        {"name": "Fresh Pineapple 1pc (~1.5kg)", "category": "fruits", "prices": {"BigBasket": 59, "Blinkit": 65, "Zepto": 62}},
        {"name": "Pineapple Sliced 200g", "category": "fruits", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
        {"name": "Baby Pineapple 1pc", "category": "fruits", "prices": {"BigBasket": 49, "Blinkit": 52, "Zepto": 50}},
    ],
    "strawberry": [
        {"name": "Fresh Strawberry 200g", "category": "fruits", "prices": {"BigBasket": 89, "Blinkit": 95, "Zepto": 92}},
        {"name": "Mahabaleshwar Strawberry 250g", "category": "fruits", "prices": {"BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Organic Strawberry 200g", "category": "fruits", "prices": {"BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
    ],
    "chikoo": [
        {"name": "Chikoo (Sapota) 500g", "category": "fruits", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
        {"name": "Chikoo Large 1kg", "category": "fruits", "prices": {"BigBasket": 89, "Blinkit": 95, "Zepto": 92}},
        {"name": "Organic Chikoo 500g", "category": "fruits", "prices": {"BigBasket": 75, "Blinkit": 79, "Zepto": 77}},
    ],
    "sapota": [
        {"name": "Chikoo (Sapota) 500g", "category": "fruits", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
    ],
    "lemon": [
        {"name": "Lemon (Nimbu) 250g (~4-5 pcs)", "category": "fruits", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Lemon 500g", "category": "fruits", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
        {"name": "Gondhoraj Lemon 250g", "category": "fruits", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "coconut": [
        {"name": "Fresh Coconut 1pc", "category": "fruits", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Tender Coconut 1pc", "category": "fruits", "prices": {"BigBasket": 45, "Blinkit": 49, "Zepto": 47}},
        {"name": "Dry Coconut (Copra) 1pc", "category": "fruits", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
    ],
    "litchi": [
        {"name": "Fresh Litchi 500g", "category": "fruits", "prices": {"BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Muzaffarpur Litchi 1kg", "category": "fruits", "prices": {"BigBasket": 219, "Blinkit": 229, "Zepto": 225}},
        {"name": "Litchi 250g", "category": "fruits", "prices": {"BigBasket": 69, "Blinkit": 75, "Zepto": 72}},
    ],
    "pear": [
        {"name": "Imported Pear (3 pcs)", "category": "fruits", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 125, "Blinkit": 132, "Zepto": 128}},
        {"name": "Indian Nashpati 500g", "category": "fruits", "prices": {"BigBasket": 69, "Blinkit": 75, "Zepto": 72}},
        {"name": "Green Pear 500g", "category": "fruits", "prices": {"BigBasket": 89, "Blinkit": 95, "Zepto": 92}},
    ],
    "plum": [
        {"name": "Fresh Plum (Aloo Bukhara) 500g", "category": "fruits", "prices": {"BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Red Plum 250g", "category": "fruits", "prices": {"BigBasket": 69, "Blinkit": 75, "Zepto": 72}},
        {"name": "Black Plum 500g", "category": "fruits", "prices": {"BigBasket": 99, "Blinkit": 105, "Zepto": 102}},
    ],
    "custard apple": [
        {"name": "Custard Apple (Sitaphal) 500g", "category": "fruits", "prices": {"BigBasket": 99, "Blinkit": 105, "Zepto": 102}},
        {"name": "Ramphal 500g", "category": "fruits", "prices": {"BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Atemoya 500g", "category": "fruits", "prices": {"BigBasket": 149, "Blinkit": 155, "Zepto": 152}},
    ],
    "fig": [
        {"name": "Fresh Fig (Anjeer) 200g", "category": "fruits", "prices": {"BigBasket": 149, "Blinkit": 155, "Zepto": 152}},
        {"name": "Dried Figs (Anjeer) 200g", "category": "fruits", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Organic Dried Figs 250g", "category": "fruits", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 275, "Blinkit": 285, "Zepto": 279}},
    ],

    # ── Vegetables ──────────────────────────────────────────────────────
    "potato": [
        {"name": "Fresh Potato (Aloo) 1kg", "category": "vegetables", "prices": {"Amazon": 39, "Flipkart": 35, "BigBasket": 30, "Blinkit": 32, "Zepto": 31}},
        {"name": "Baby Potato 500g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Red Potato 1kg", "category": "vegetables", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
    ],
    "onion": [
        {"name": "Onion (Pyaaz) 1kg", "category": "vegetables", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Red Onion 1kg", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Shallots (Sambar Onion) 500g", "category": "vegetables", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
    ],
    "tomato": [
        {"name": "Tomato (Tamatar) 1kg", "category": "vegetables", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 38, "Blinkit": 40, "Zepto": 39}},
        {"name": "Hybrid Tomato 500g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Cherry Tomato 200g", "category": "vegetables", "prices": {"BigBasket": 49, "Blinkit": 52, "Zepto": 50}},
    ],
    "carrot": [
        {"name": "Fresh Carrot (Gajar) 500g", "category": "vegetables", "prices": {"Amazon": 39, "Flipkart": 35, "BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Ooty Carrot 500g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Red Carrot 1kg", "category": "vegetables", "prices": {"BigBasket": 49, "Blinkit": 52, "Zepto": 50}},
    ],
    "capsicum": [
        {"name": "Green Capsicum (Shimla Mirch) 250g", "category": "vegetables", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Red Capsicum 1pc (~150g)", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Yellow Capsicum 1pc (~150g)", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
    ],
    "brinjal": [
        {"name": "Brinjal (Baingan) 500g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Long Brinjal 500g", "category": "vegetables", "prices": {"BigBasket": 32, "Blinkit": 35, "Zepto": 33}},
        {"name": "Round Brinjal 500g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
    ],
    "baingan": [
        {"name": "Brinjal (Baingan) 500g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
    ],
    "cauliflower": [
        {"name": "Cauliflower (Phool Gobi) 1pc", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Baby Cauliflower 1pc", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Organic Cauliflower 1pc", "category": "vegetables", "prices": {"BigBasket": 49, "Blinkit": 52, "Zepto": 50}},
    ],
    "cabbage": [
        {"name": "Cabbage (Patta Gobi) 1pc (~500g)", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Red Cabbage 1pc (~400g)", "category": "vegetables", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
        {"name": "Chinese Cabbage 1pc", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
    ],
    "spinach": [
        {"name": "Spinach (Palak) 250g", "category": "vegetables", "prices": {"BigBasket": 22, "Blinkit": 25, "Zepto": 23}},
        {"name": "Baby Spinach 100g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Organic Palak 250g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "palak": [
        {"name": "Spinach (Palak) 250g", "category": "vegetables", "prices": {"BigBasket": 22, "Blinkit": 25, "Zepto": 23}},
    ],
    "peas": [
        {"name": "Green Peas (Matar) 250g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Fresh Green Peas 500g", "category": "vegetables", "prices": {"BigBasket": 59, "Blinkit": 62, "Zepto": 60}},
        {"name": "Snow Peas 200g", "category": "vegetables", "prices": {"BigBasket": 69, "Blinkit": 75, "Zepto": 72}},
    ],
    "beans": [
        {"name": "French Beans 250g", "category": "vegetables", "prices": {"BigBasket": 32, "Blinkit": 35, "Zepto": 33}},
        {"name": "Broad Beans (Sem) 250g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Cluster Beans (Gawar) 250g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "french beans": [
        {"name": "French Beans 250g", "category": "vegetables", "prices": {"BigBasket": 32, "Blinkit": 35, "Zepto": 33}},
    ],
    "lady finger": [
        {"name": "Lady Finger (Bhindi) 250g", "category": "vegetables", "prices": {"BigBasket": 28, "Blinkit": 30, "Zepto": 29}},
        {"name": "Baby Bhindi 250g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Organic Lady Finger 250g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
    ],
    "bhindi": [
        {"name": "Lady Finger (Bhindi) 250g", "category": "vegetables", "prices": {"BigBasket": 28, "Blinkit": 30, "Zepto": 29}},
    ],
    "cucumber": [
        {"name": "Cucumber (Kheera) 500g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "English Cucumber 1pc", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Organic Cucumber 500g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
    ],
    "ginger": [
        {"name": "Fresh Ginger (Adrak) 100g", "category": "vegetables", "prices": {"BigBasket": 19, "Blinkit": 22, "Zepto": 20}},
        {"name": "Ginger 250g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Organic Ginger 100g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
    ],
    "garlic": [
        {"name": "Garlic (Lahsun) 250g", "category": "vegetables", "prices": {"Amazon": 55, "Flipkart": 49, "BigBasket": 42, "Blinkit": 45, "Zepto": 43}},
        {"name": "Garlic Peeled 100g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Kashmiri Garlic 100g", "category": "vegetables", "prices": {"Amazon": 89, "BigBasket": 79, "Blinkit": 85, "Zepto": 82}},
    ],
    "beetroot": [
        {"name": "Beetroot (Chukandar) 500g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Baby Beetroot 250g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Organic Beetroot 500g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
    ],
    "radish": [
        {"name": "Radish (Mooli) 500g", "category": "vegetables", "prices": {"BigBasket": 19, "Blinkit": 22, "Zepto": 20}},
        {"name": "Red Radish 250g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "White Radish 1kg", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
    ],
    "mooli": [
        {"name": "Radish (Mooli) 500g", "category": "vegetables", "prices": {"BigBasket": 19, "Blinkit": 22, "Zepto": 20}},
    ],
    "bitter gourd": [
        {"name": "Bitter Gourd (Karela) 250g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Baby Karela 250g", "category": "vegetables", "prices": {"BigBasket": 32, "Blinkit": 35, "Zepto": 33}},
        {"name": "Organic Bitter Gourd 250g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "karela": [
        {"name": "Bitter Gourd (Karela) 250g", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
    ],
    "bottle gourd": [
        {"name": "Bottle Gourd (Lauki) 1pc (~500g)", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Round Bottle Gourd 1pc", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Organic Lauki 1pc", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "lauki": [
        {"name": "Bottle Gourd (Lauki) 1pc (~500g)", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
    ],
    "ridge gourd": [
        {"name": "Ridge Gourd (Turai) 250g", "category": "vegetables", "prices": {"BigBasket": 22, "Blinkit": 25, "Zepto": 23}},
        {"name": "Peeled Ridge Gourd 250g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Organic Turai 250g", "category": "vegetables", "prices": {"BigBasket": 32, "Blinkit": 35, "Zepto": 33}},
    ],
    "turai": [
        {"name": "Ridge Gourd (Turai) 250g", "category": "vegetables", "prices": {"BigBasket": 22, "Blinkit": 25, "Zepto": 23}},
    ],
    "drumstick": [
        {"name": "Drumstick (Sahjan) 250g", "category": "vegetables", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "Fresh Drumstick 500g", "category": "vegetables", "prices": {"BigBasket": 49, "Blinkit": 52, "Zepto": 50}},
        {"name": "Organic Drumstick 250g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
    ],
    "mushroom": [
        {"name": "Button Mushroom 200g", "category": "vegetables", "prices": {"Amazon": 49, "BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Oyster Mushroom 200g", "category": "vegetables", "prices": {"BigBasket": 59, "Blinkit": 62, "Zepto": 60}},
        {"name": "Shiitake Mushroom 100g", "category": "vegetables", "prices": {"BigBasket": 99, "Blinkit": 105, "Zepto": 102}},
    ],
    "sweet potato": [
        {"name": "Sweet Potato (Shakarkandi) 500g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
        {"name": "Orange Sweet Potato 500g", "category": "vegetables", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
        {"name": "Purple Sweet Potato 500g", "category": "vegetables", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
    ],
    "corn": [
        {"name": "Sweet Corn 1pc", "category": "vegetables", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
        {"name": "Baby Corn 200g", "category": "vegetables", "prices": {"BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Sweet Corn Kernels 200g", "category": "vegetables", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "coriander": [
        {"name": "Coriander (Dhaniya) Leaves 100g", "category": "vegetables", "prices": {"BigBasket": 12, "Blinkit": 15, "Zepto": 13}},
        {"name": "Fresh Coriander Bunch", "category": "vegetables", "prices": {"BigBasket": 10, "Blinkit": 12, "Zepto": 11}},
        {"name": "Organic Coriander 100g", "category": "vegetables", "prices": {"BigBasket": 19, "Blinkit": 22, "Zepto": 20}},
    ],
    "dhaniya": [
        {"name": "Coriander (Dhaniya) Leaves 100g", "category": "vegetables", "prices": {"BigBasket": 12, "Blinkit": 15, "Zepto": 13}},
    ],
    "mint": [
        {"name": "Mint (Pudina) Leaves 100g", "category": "vegetables", "prices": {"BigBasket": 12, "Blinkit": 15, "Zepto": 13}},
        {"name": "Fresh Mint Bunch", "category": "vegetables", "prices": {"BigBasket": 10, "Blinkit": 12, "Zepto": 11}},
        {"name": "Organic Pudina 100g", "category": "vegetables", "prices": {"BigBasket": 19, "Blinkit": 22, "Zepto": 20}},
    ],
    "pudina": [
        {"name": "Mint (Pudina) Leaves 100g", "category": "vegetables", "prices": {"BigBasket": 12, "Blinkit": 15, "Zepto": 13}},
    ],
    "curry leaves": [
        {"name": "Curry Leaves (Kadi Patta) 50g", "category": "vegetables", "prices": {"BigBasket": 10, "Blinkit": 12, "Zepto": 11}},
        {"name": "Fresh Curry Leaves Bunch", "category": "vegetables", "prices": {"BigBasket": 8, "Blinkit": 10, "Zepto": 9}},
        {"name": "Organic Curry Leaves 50g", "category": "vegetables", "prices": {"BigBasket": 15, "Blinkit": 18, "Zepto": 16}},
    ],
    "green chilli": [
        {"name": "Green Chilli 100g", "category": "vegetables", "prices": {"BigBasket": 10, "Blinkit": 12, "Zepto": 11}},
        {"name": "Bird's Eye Chilli 50g", "category": "vegetables", "prices": {"BigBasket": 15, "Blinkit": 18, "Zepto": 16}},
        {"name": "Jwala Green Chilli 100g", "category": "vegetables", "prices": {"BigBasket": 12, "Blinkit": 15, "Zepto": 13}},
    ],

    # ── Dairy & Eggs ────────────────────────────────────────────────────
    "milk": [
        {"name": "Amul Taaza Toned Milk 1L", "category": "dairy", "prices": {"Amazon": 66, "BigBasket": 62, "Blinkit": 62, "Zepto": 62}},
        {"name": "Mother Dairy Full Cream Milk 1L", "category": "dairy", "prices": {"BigBasket": 68, "Blinkit": 68, "Zepto": 68}},
        {"name": "Amul Gold Full Cream Milk 1L", "category": "dairy", "prices": {"BigBasket": 72, "Blinkit": 72, "Zepto": 72}},
        {"name": "Amul Double Toned Milk 1L", "category": "dairy", "prices": {"BigBasket": 54, "Blinkit": 54, "Zepto": 54}},
        {"name": "Nandini Toned Milk 1L", "category": "dairy", "prices": {"BigBasket": 48, "Blinkit": 50, "Zepto": 49}},
    ],
    "curd": [
        {"name": "Amul Masti Dahi 400g", "category": "dairy", "prices": {"BigBasket": 35, "Blinkit": 33, "Zepto": 33}},
        {"name": "Mother Dairy Classic Curd 400g", "category": "dairy", "prices": {"BigBasket": 32, "Blinkit": 30, "Zepto": 30}},
        {"name": "Nestle a+ Curd 400g", "category": "dairy", "prices": {"BigBasket": 38, "Blinkit": 36, "Zepto": 36}},
    ],
    "dahi": [
        {"name": "Amul Masti Dahi 400g", "category": "dairy", "prices": {"BigBasket": 35, "Blinkit": 33, "Zepto": 33}},
    ],
    "paneer": [
        {"name": "Amul Fresh Paneer 200g", "category": "dairy", "prices": {"Amazon": 95, "BigBasket": 85, "Blinkit": 88, "Zepto": 86}},
        {"name": "Mother Dairy Paneer 200g", "category": "dairy", "prices": {"BigBasket": 80, "Blinkit": 82, "Zepto": 80}},
        {"name": "Amul Malai Paneer 1kg", "category": "dairy", "prices": {"Amazon": 399, "BigBasket": 379, "Blinkit": 389, "Zepto": 385}},
    ],
    "butter": [
        {"name": "Amul Butter 500g", "category": "dairy", "prices": {"Amazon": 275, "Flipkart": 270, "BigBasket": 265, "Blinkit": 268, "Zepto": 267}},
        {"name": "Amul Butter 100g", "category": "dairy", "prices": {"Amazon": 57, "Flipkart": 56, "BigBasket": 54, "Blinkit": 55, "Zepto": 54}},
        {"name": "Britannia Bread Butter 100g", "category": "dairy", "prices": {"Amazon": 52, "Flipkart": 50, "BigBasket": 48, "Blinkit": 49, "Zepto": 48}},
    ],
    "ghee": [
        {"name": "Amul Pure Ghee 1L", "category": "dairy", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 565, "Blinkit": 575, "Zepto": 570}},
        {"name": "Patanjali Cow Ghee 1L", "category": "dairy", "prices": {"Amazon": 549, "Flipkart": 539, "BigBasket": 525, "Blinkit": 535, "Zepto": 530}},
        {"name": "Gowardhan Pure Cow Ghee 1L", "category": "dairy", "prices": {"Amazon": 619, "Flipkart": 599, "BigBasket": 585, "Blinkit": 595, "Zepto": 589}},
    ],
    "cheese": [
        {"name": "Amul Cheese Slices 200g (10 Slices)", "category": "dairy", "prices": {"Amazon": 120, "Flipkart": 115, "BigBasket": 105, "Blinkit": 110, "Zepto": 108}},
        {"name": "Britannia Cheese Block 200g", "category": "dairy", "prices": {"Amazon": 110, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
        {"name": "Amul Cheese Spread 200g", "category": "dairy", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Gouda Cheese 200g", "category": "dairy", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 275, "Blinkit": 285, "Zepto": 279}},
    ],
    "cream": [
        {"name": "Amul Fresh Cream 200ml", "category": "dairy", "prices": {"Amazon": 65, "BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
        {"name": "Amul Whipping Cream 250ml", "category": "dairy", "prices": {"Amazon": 99, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Rich's Non-Dairy Whipping Cream 1L", "category": "dairy", "prices": {"Amazon": 349, "BigBasket": 329, "Blinkit": 339, "Zepto": 335}},
    ],
    "buttermilk": [
        {"name": "Amul Masti Buttermilk 200ml", "category": "dairy", "prices": {"BigBasket": 15, "Blinkit": 15, "Zepto": 15}},
        {"name": "Mother Dairy Chaach 500ml", "category": "dairy", "prices": {"BigBasket": 25, "Blinkit": 25, "Zepto": 25}},
        {"name": "Amul Masti Spiced Buttermilk 1L", "category": "dairy", "prices": {"BigBasket": 35, "Blinkit": 35, "Zepto": 35}},
    ],
    "chaas": [
        {"name": "Mother Dairy Chaach 500ml", "category": "dairy", "prices": {"BigBasket": 25, "Blinkit": 25, "Zepto": 25}},
    ],
    "eggs": [
        {"name": "Farm Fresh White Eggs (Pack of 12)", "category": "dairy", "prices": {"BigBasket": 79, "Blinkit": 75, "Zepto": 76}},
        {"name": "Country Eggs Brown (Pack of 6)", "category": "dairy", "prices": {"BigBasket": 65, "Blinkit": 62, "Zepto": 63}},
        {"name": "Organic Free Range Eggs (Pack of 6)", "category": "dairy", "prices": {"Amazon": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Farm Fresh White Eggs (Pack of 30)", "category": "dairy", "prices": {"Amazon": 219, "BigBasket": 199, "Blinkit": 209, "Zepto": 205}},
    ],
    "yogurt": [
        {"name": "Epigamia Greek Yogurt 90g", "category": "dairy", "prices": {"Amazon": 55, "BigBasket": 49, "Blinkit": 50, "Zepto": 49}},
        {"name": "Amul Misti Doi 400g", "category": "dairy", "prices": {"BigBasket": 55, "Blinkit": 52, "Zepto": 53}},
        {"name": "Epigamia Greek Yogurt Strawberry 90g", "category": "dairy", "prices": {"Amazon": 55, "BigBasket": 49, "Blinkit": 50, "Zepto": 49}},
    ],

    # ── Staples & Grains ────────────────────────────────────────────────
    "rice": [
        {"name": "India Gate Basmati Rice 5kg", "category": "staples", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 569, "Blinkit": 589, "Zepto": 575}},
        {"name": "Daawat Rozana Basmati Rice 5kg", "category": "staples", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 445, "Zepto": 435}},
        {"name": "24 Mantra Organic Sona Masoori Rice 5kg", "category": "staples", "prices": {"Amazon": 499, "Flipkart": 489, "BigBasket": 479, "Blinkit": 489, "Zepto": 485}},
        {"name": "India Gate Brown Rice 1kg", "category": "staples", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "atta": [
        {"name": "Aashirvaad Atta 10kg", "category": "staples", "prices": {"Amazon": 489, "Flipkart": 479, "BigBasket": 469, "Blinkit": 485, "Zepto": 475}},
        {"name": "Fortune Chakki Fresh Atta 5kg", "category": "staples", "prices": {"Amazon": 265, "Flipkart": 259, "BigBasket": 249, "Blinkit": 255, "Zepto": 252}},
        {"name": "Pillsbury Atta 5kg", "category": "staples", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],
    "wheat flour": [
        {"name": "Aashirvaad Atta 10kg", "category": "staples", "prices": {"Amazon": 489, "Flipkart": 479, "BigBasket": 469, "Blinkit": 485, "Zepto": 475}},
        {"name": "Fortune Chakki Fresh Atta 5kg", "category": "staples", "prices": {"Amazon": 265, "Flipkart": 259, "BigBasket": 249, "Blinkit": 255, "Zepto": 252}},
    ],
    "toor dal": [
        {"name": "Tata Sampann Toor Dal 1kg", "category": "staples", "prices": {"Amazon": 179, "Flipkart": 175, "BigBasket": 169, "Blinkit": 172, "Zepto": 170}},
        {"name": "Fortune Arhar Dal (Toor) 1kg", "category": "staples", "prices": {"Amazon": 165, "Flipkart": 162, "BigBasket": 159, "Blinkit": 164, "Zepto": 160}},
        {"name": "BB Royal Toor Dal 1kg", "category": "staples", "prices": {"BigBasket": 145, "Blinkit": 150, "Zepto": 148}},
    ],
    "moong dal": [
        {"name": "Tata Sampann Moong Dal 1kg", "category": "staples", "prices": {"Amazon": 169, "Flipkart": 165, "BigBasket": 159, "Blinkit": 162, "Zepto": 160}},
        {"name": "BB Royal Moong Dal 1kg", "category": "staples", "prices": {"BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
        {"name": "24 Mantra Organic Moong Dal 500g", "category": "staples", "prices": {"Amazon": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
    ],
    "chana dal": [
        {"name": "Tata Sampann Chana Dal 1kg", "category": "staples", "prices": {"Amazon": 139, "Flipkart": 135, "BigBasket": 129, "Blinkit": 132, "Zepto": 130}},
        {"name": "BB Royal Chana Dal 1kg", "category": "staples", "prices": {"BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Fortune Chana Dal 1kg", "category": "staples", "prices": {"Amazon": 129, "Flipkart": 125, "BigBasket": 119, "Blinkit": 122, "Zepto": 120}},
    ],
    "urad dal": [
        {"name": "Tata Sampann Urad Dal 1kg", "category": "staples", "prices": {"Amazon": 189, "Flipkart": 185, "BigBasket": 179, "Blinkit": 182, "Zepto": 180}},
        {"name": "BB Royal Urad Dal 1kg", "category": "staples", "prices": {"BigBasket": 165, "Blinkit": 172, "Zepto": 168}},
        {"name": "24 Mantra Organic Urad Dal 500g", "category": "staples", "prices": {"Amazon": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
    ],
    "masoor dal": [
        {"name": "Tata Sampann Masoor Dal 1kg", "category": "staples", "prices": {"Amazon": 129, "Flipkart": 125, "BigBasket": 119, "Blinkit": 122, "Zepto": 120}},
        {"name": "BB Royal Masoor Dal 1kg", "category": "staples", "prices": {"BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Fortune Masoor Dal 1kg", "category": "staples", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
    ],
    "rajma": [
        {"name": "Tata Sampann Rajma 500g", "category": "staples", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
        {"name": "BB Royal Rajma Chitra 1kg", "category": "staples", "prices": {"Amazon": 189, "Flipkart": 179, "BigBasket": 169, "Blinkit": 175, "Zepto": 172}},
        {"name": "Kashmiri Rajma 1kg", "category": "staples", "prices": {"Amazon": 219, "Flipkart": 209, "BigBasket": 199, "Blinkit": 205, "Zepto": 202}},
    ],
    "chole": [
        {"name": "Tata Sampann Kabuli Chana 500g", "category": "staples", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "BB Royal Kabuli Chana 1kg", "category": "staples", "prices": {"Amazon": 169, "Flipkart": 159, "BigBasket": 149, "Blinkit": 155, "Zepto": 152}},
        {"name": "Organic Kabuli Chana 500g", "category": "staples", "prices": {"Amazon": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
    ],
    "chickpeas": [
        {"name": "Tata Sampann Kabuli Chana 500g", "category": "staples", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "poha": [
        {"name": "BB Royal Poha (Flattened Rice) Thick 500g", "category": "staples", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 38, "Blinkit": 40, "Zepto": 39}},
        {"name": "Aashirvaad Poha 500g", "category": "staples", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
        {"name": "Thin Poha 500g", "category": "staples", "prices": {"Amazon": 42, "Flipkart": 39, "BigBasket": 35, "Blinkit": 37, "Zepto": 36}},
    ],
    "sooji": [
        {"name": "BB Royal Sooji (Rava) 500g", "category": "staples", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
        {"name": "Aashirvaad Sooji 1kg", "category": "staples", "prices": {"Amazon": 65, "Flipkart": 62, "BigBasket": 58, "Blinkit": 60, "Zepto": 59}},
        {"name": "Roasted Sooji 500g", "category": "staples", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 38, "Blinkit": 40, "Zepto": 39}},
    ],
    "rava": [
        {"name": "BB Royal Sooji (Rava) 500g", "category": "staples", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
    ],
    "besan": [
        {"name": "BB Royal Besan (Gram Flour) 500g", "category": "staples", "prices": {"Amazon": 55, "Flipkart": 52, "BigBasket": 48, "Blinkit": 50, "Zepto": 49}},
        {"name": "Aashirvaad Besan 1kg", "category": "staples", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Organic Besan 500g", "category": "staples", "prices": {"Amazon": 79, "BigBasket": 69, "Blinkit": 75, "Zepto": 72}},
    ],
    "maida": [
        {"name": "Aashirvaad Maida 1kg", "category": "staples", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 42, "Blinkit": 44, "Zepto": 43}},
        {"name": "Pillsbury Maida 1kg", "category": "staples", "prices": {"Amazon": 52, "Flipkart": 49, "BigBasket": 45, "Blinkit": 47, "Zepto": 46}},
        {"name": "BB Royal Maida 500g", "category": "staples", "prices": {"Amazon": 29, "Flipkart": 26, "BigBasket": 22, "Blinkit": 24, "Zepto": 23}},
    ],
    "oats": [
        {"name": "Quaker Oats 1kg", "category": "staples", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Saffola Masala Oats 500g", "category": "staples", "prices": {"Amazon": 169, "Flipkart": 159, "BigBasket": 149, "Blinkit": 155, "Zepto": 152}},
        {"name": "Bagrry's White Oats 1kg", "category": "staples", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "cornflakes": [
        {"name": "Kellogg's Corn Flakes Original 475g", "category": "staples", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Kellogg's Chocos 375g", "category": "staples", "prices": {"Amazon": 219, "Flipkart": 209, "BigBasket": 199, "Blinkit": 205, "Zepto": 202}},
        {"name": "Bagrry's Corn Flakes Plus 800g", "category": "staples", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],
    "muesli": [
        {"name": "Bagrry's Crunchy Muesli 750g", "category": "staples", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 379, "Blinkit": 385, "Zepto": 382}},
        {"name": "Kellogg's Muesli Fruit & Nut 750g", "category": "staples", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 435, "Zepto": 432}},
        {"name": "Yoga Bar Muesli 700g", "category": "staples", "prices": {"Amazon": 499, "Flipkart": 489, "BigBasket": 479, "Blinkit": 485, "Zepto": 482}},
    ],
    "sugar": [
        {"name": "Madhur Pure Sugar 1kg", "category": "staples", "prices": {"Amazon": 49, "Flipkart": 47, "BigBasket": 45, "Blinkit": 46, "Zepto": 45}},
        {"name": "Trust Classic Sugar 5kg", "category": "staples", "prices": {"Amazon": 235, "Flipkart": 229, "BigBasket": 225, "Blinkit": 230, "Zepto": 228}},
        {"name": "Organic Sugar 1kg", "category": "staples", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
    ],

    # ── Cooking Essentials ──────────────────────────────────────────────
    "sunflower oil": [
        {"name": "Fortune Sunlite Refined Sunflower Oil 1L", "category": "cooking", "prices": {"Amazon": 145, "Flipkart": 139, "BigBasket": 135, "Blinkit": 140, "Zepto": 137}},
        {"name": "Freedom Refined Sunflower Oil 1L", "category": "cooking", "prices": {"Amazon": 135, "Flipkart": 129, "BigBasket": 125, "Blinkit": 130, "Zepto": 127}},
        {"name": "Nature Fresh Sunflower Oil 5L", "category": "cooking", "prices": {"Amazon": 649, "Flipkart": 629, "BigBasket": 619, "Blinkit": 639, "Zepto": 625}},
    ],
    "mustard oil": [
        {"name": "Fortune Kachi Ghani Mustard Oil 1L", "category": "cooking", "prices": {"Amazon": 179, "Flipkart": 175, "BigBasket": 169, "Blinkit": 172, "Zepto": 170}},
        {"name": "Patanjali Mustard Oil 1L", "category": "cooking", "prices": {"Amazon": 165, "Flipkart": 159, "BigBasket": 155, "Blinkit": 158, "Zepto": 156}},
        {"name": "Engine Mustard Oil 1L", "category": "cooking", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 165, "Blinkit": 168, "Zepto": 166}},
    ],
    "groundnut oil": [
        {"name": "Fortune Groundnut Oil 1L", "category": "cooking", "prices": {"Amazon": 219, "Flipkart": 209, "BigBasket": 199, "Blinkit": 205, "Zepto": 202}},
        {"name": "Gemini Groundnut Oil 1L", "category": "cooking", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Organic Groundnut Oil 1L", "category": "cooking", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
    ],
    "olive oil": [
        {"name": "Figaro Extra Virgin Olive Oil 500ml", "category": "cooking", "prices": {"Amazon": 499, "Flipkart": 479, "BigBasket": 465, "Blinkit": 475, "Zepto": 470}},
        {"name": "Borges Extra Virgin Olive Oil 500ml", "category": "cooking", "prices": {"Amazon": 549, "Flipkart": 529, "BigBasket": 515, "Blinkit": 525, "Zepto": 520}},
        {"name": "Del Monte Olive Oil 1L", "category": "cooking", "prices": {"Amazon": 799, "Flipkart": 779, "BigBasket": 759, "Blinkit": 775, "Zepto": 769}},
    ],
    "coconut oil": [
        {"name": "Parachute Coconut Oil 600ml", "category": "cooking", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "KLF Coconad Pure Coconut Oil 1L", "category": "cooking", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Organic Virgin Coconut Oil 500ml", "category": "cooking", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 379, "Blinkit": 385, "Zepto": 382}},
    ],
    "oil": [
        {"name": "Fortune Sunlite Refined Sunflower Oil 1L", "category": "cooking", "prices": {"Amazon": 145, "Flipkart": 139, "BigBasket": 135, "Blinkit": 140, "Zepto": 137}},
        {"name": "Saffola Gold Edible Oil 1L", "category": "cooking", "prices": {"Amazon": 189, "Flipkart": 185, "BigBasket": 179, "Blinkit": 182, "Zepto": 180}},
        {"name": "Fortune Rice Bran Oil 1L", "category": "cooking", "prices": {"Amazon": 159, "Flipkart": 149, "BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
    ],
    "salt": [
        {"name": "Tata Salt 1kg", "category": "cooking", "prices": {"Amazon": 28, "Flipkart": 25, "BigBasket": 22, "Blinkit": 24, "Zepto": 23}},
        {"name": "Tata Rock Salt 1kg", "category": "cooking", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
        {"name": "Catch Black Salt 200g", "category": "cooking", "prices": {"Amazon": 35, "Flipkart": 32, "BigBasket": 29, "Blinkit": 30, "Zepto": 29}},
    ],
    "jaggery": [
        {"name": "Organic Jaggery (Gur) 1kg", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Jaggery Powder 500g", "category": "cooking", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "Palm Jaggery 500g", "category": "cooking", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "gur": [
        {"name": "Organic Jaggery (Gur) 1kg", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "turmeric": [
        {"name": "MDH Turmeric Powder 100g", "category": "cooking", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 42, "Blinkit": 44, "Zepto": 43}},
        {"name": "Everest Turmeric Powder 200g", "category": "cooking", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Organic Turmeric Powder 200g", "category": "cooking", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "haldi": [
        {"name": "MDH Turmeric Powder 100g", "category": "cooking", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 42, "Blinkit": 44, "Zepto": 43}},
    ],
    "chilli powder": [
        {"name": "MDH Deggi Mirch 100g", "category": "cooking", "prices": {"Amazon": 65, "Flipkart": 62, "BigBasket": 58, "Blinkit": 60, "Zepto": 59}},
        {"name": "Everest Kashmirilal Chilli Powder 100g", "category": "cooking", "prices": {"Amazon": 75, "Flipkart": 72, "BigBasket": 68, "Blinkit": 70, "Zepto": 69}},
        {"name": "Catch Red Chilli Powder 200g", "category": "cooking", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "red chilli powder": [
        {"name": "MDH Deggi Mirch 100g", "category": "cooking", "prices": {"Amazon": 65, "Flipkart": 62, "BigBasket": 58, "Blinkit": 60, "Zepto": 59}},
    ],
    "cumin": [
        {"name": "MDH Cumin (Jeera) Powder 100g", "category": "cooking", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Whole Cumin Seeds (Jeera) 200g", "category": "cooking", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
        {"name": "Organic Cumin Seeds 100g", "category": "cooking", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "jeera": [
        {"name": "Whole Cumin Seeds (Jeera) 200g", "category": "cooking", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
    ],
    "coriander powder": [
        {"name": "MDH Coriander Powder 100g", "category": "cooking", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 42, "Blinkit": 44, "Zepto": 43}},
        {"name": "Everest Coriander Powder 200g", "category": "cooking", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Catch Coriander Powder 200g", "category": "cooking", "prices": {"Amazon": 69, "Flipkart": 65, "BigBasket": 59, "Blinkit": 62, "Zepto": 60}},
    ],
    "garam masala": [
        {"name": "MDH Garam Masala 100g", "category": "cooking", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "Everest Garam Masala 100g", "category": "cooking", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Catch Garam Masala 200g", "category": "cooking", "prices": {"Amazon": 139, "Flipkart": 135, "BigBasket": 129, "Blinkit": 132, "Zepto": 130}},
    ],
    "black pepper": [
        {"name": "Catch Black Pepper Powder 100g", "category": "cooking", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
        {"name": "Whole Black Pepper 100g", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Organic Black Pepper 50g", "category": "cooking", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "bay leaves": [
        {"name": "Catch Bay Leaves (Tej Patta) 50g", "category": "cooking", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 39, "Blinkit": 42, "Zepto": 40}},
        {"name": "Organic Bay Leaves 25g", "category": "cooking", "prices": {"Amazon": 39, "Flipkart": 35, "BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
        {"name": "BB Royal Bay Leaves 50g", "category": "cooking", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "cinnamon": [
        {"name": "Catch Cinnamon (Dalchini) 50g", "category": "cooking", "prices": {"Amazon": 69, "Flipkart": 65, "BigBasket": 59, "Blinkit": 62, "Zepto": 60}},
        {"name": "Whole Cinnamon Sticks 100g", "category": "cooking", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
        {"name": "Organic Ceylon Cinnamon 50g", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "cardamom": [
        {"name": "Catch Green Cardamom (Elaichi) 25g", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Whole Green Cardamom 50g", "category": "cooking", "prices": {"Amazon": 279, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
        {"name": "Black Cardamom 25g", "category": "cooking", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "cloves": [
        {"name": "Catch Cloves (Laung) 25g", "category": "cooking", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Whole Cloves 50g", "category": "cooking", "prices": {"Amazon": 139, "Flipkart": 135, "BigBasket": 129, "Blinkit": 132, "Zepto": 130}},
        {"name": "Organic Cloves 25g", "category": "cooking", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "vinegar": [
        {"name": "American Garden White Vinegar 473ml", "category": "cooking", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Borges Apple Cider Vinegar 500ml", "category": "cooking", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Dabur Apple Cider Vinegar 500ml", "category": "cooking", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "soy sauce": [
        {"name": "Ching's Dark Soy Sauce 200g", "category": "cooking", "prices": {"Amazon": 55, "Flipkart": 52, "BigBasket": 48, "Blinkit": 50, "Zepto": 49}},
        {"name": "Kikkoman Soy Sauce 150ml", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Weikfield Soy Sauce 200g", "category": "cooking", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 38, "Blinkit": 40, "Zepto": 39}},
    ],
    "tomato ketchup": [
        {"name": "Kissan Fresh Tomato Ketchup 950g", "category": "cooking", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Maggi Hot & Sweet Ketchup 1kg", "category": "cooking", "prices": {"Amazon": 159, "Flipkart": 149, "BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
        {"name": "Del Monte Tomato Ketchup 500g", "category": "cooking", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],

    # ── Snacks & Namkeen ────────────────────────────────────────────────
    "chips": [
        {"name": "Lay's Classic Salted Chips 52g", "category": "snacks", "prices": {"Amazon": 20, "Flipkart": 20, "BigBasket": 18, "Blinkit": 20, "Zepto": 20}},
        {"name": "Kurkure Masala Munch 100g", "category": "snacks", "prices": {"Amazon": 25, "Flipkart": 25, "BigBasket": 22, "Blinkit": 24, "Zepto": 23}},
        {"name": "Bingo Mad Angles 72.5g", "category": "snacks", "prices": {"Amazon": 20, "Flipkart": 20, "BigBasket": 18, "Blinkit": 20, "Zepto": 20}},
        {"name": "Lay's Magic Masala 52g", "category": "snacks", "prices": {"Amazon": 20, "Flipkart": 20, "BigBasket": 18, "Blinkit": 20, "Zepto": 20}},
    ],
    "namkeen": [
        {"name": "Haldiram's Aloo Bhujia 400g", "category": "snacks", "prices": {"Amazon": 135, "Flipkart": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Haldiram's Moong Dal 400g", "category": "snacks", "prices": {"Amazon": 125, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Bikaji Bhujia Sev 400g", "category": "snacks", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
        {"name": "Haldiram's Mixture 400g", "category": "snacks", "prices": {"Amazon": 129, "Flipkart": 125, "BigBasket": 115, "Blinkit": 119, "Zepto": 117}},
    ],
    "biscuit": [
        {"name": "Parle-G Gold Biscuits 1kg", "category": "snacks", "prices": {"Amazon": 115, "Flipkart": 110, "BigBasket": 105, "Blinkit": 108, "Zepto": 106}},
        {"name": "Britannia Marie Gold 600g", "category": "snacks", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Britannia Good Day Cashew 600g", "category": "snacks", "prices": {"Amazon": 165, "Flipkart": 159, "BigBasket": 155, "Blinkit": 158, "Zepto": 156}},
        {"name": "Britannia Bourbon 300g", "category": "snacks", "prices": {"Amazon": 55, "Flipkart": 52, "BigBasket": 48, "Blinkit": 50, "Zepto": 49}},
    ],
    "biscuits": [
        {"name": "Parle-G Gold Biscuits 1kg", "category": "snacks", "prices": {"Amazon": 115, "Flipkart": 110, "BigBasket": 105, "Blinkit": 108, "Zepto": 106}},
        {"name": "Britannia Marie Gold 600g", "category": "snacks", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "cookies": [
        {"name": "Britannia Good Day Choco Chip 600g", "category": "snacks", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Unibic Choco Chip Cookies 500g", "category": "snacks", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Sunfeast Dark Fantasy 300g", "category": "snacks", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "chocolate": [
        {"name": "Cadbury Dairy Milk Silk 150g", "category": "snacks", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Cadbury Dairy Milk 110g", "category": "snacks", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "KitKat 4 Finger 37.3g (Pack of 6)", "category": "snacks", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Cadbury 5 Star 3D 42g (Pack of 10)", "category": "snacks", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "almonds": [
        {"name": "Happilo Premium California Almonds 200g", "category": "snacks", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Nutraj California Almonds 500g", "category": "snacks", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 435, "Zepto": 432}},
        {"name": "Farmley Premium Almonds 250g", "category": "snacks", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],
    "cashews": [
        {"name": "Happilo Premium Cashews 200g", "category": "snacks", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Nutraj Whole Cashews W320 500g", "category": "snacks", "prices": {"Amazon": 549, "Flipkart": 529, "BigBasket": 519, "Blinkit": 535, "Zepto": 525}},
        {"name": "Farmley Premium Cashews 250g", "category": "snacks", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
    ],
    "raisins": [
        {"name": "Happilo Premium Raisins 250g", "category": "snacks", "prices": {"Amazon": 119, "Flipkart": 109, "BigBasket": 99, "Blinkit": 105, "Zepto": 102}},
        {"name": "Nutraj Afghan Raisins 500g", "category": "snacks", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Golden Raisins 200g", "category": "snacks", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "walnuts": [
        {"name": "Happilo Premium Walnuts 200g", "category": "snacks", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Nutraj Kashmir Walnuts 500g", "category": "snacks", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 569, "Blinkit": 585, "Zepto": 575}},
        {"name": "Organic Walnuts 250g", "category": "snacks", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
    ],
    "pistachios": [
        {"name": "Happilo Premium Pistachios 200g", "category": "snacks", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
        {"name": "Nutraj Iranian Pistachios 250g", "category": "snacks", "prices": {"Amazon": 499, "Flipkart": 489, "BigBasket": 479, "Blinkit": 485, "Zepto": 482}},
        {"name": "Salted Pistachios 200g", "category": "snacks", "prices": {"Amazon": 379, "Flipkart": 369, "BigBasket": 359, "Blinkit": 365, "Zepto": 362}},
    ],
    "dry fruits": [
        {"name": "Happilo Premium Dry Fruits Mix 200g", "category": "snacks", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Nutraj Mixed Dry Fruits 500g", "category": "snacks", "prices": {"Amazon": 549, "Flipkart": 529, "BigBasket": 519, "Blinkit": 535, "Zepto": 525}},
        {"name": "Farmley Premium Trail Mix 200g", "category": "snacks", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],

    # ── Beverages ───────────────────────────────────────────────────────
    "tea": [
        {"name": "Tata Tea Gold 500g", "category": "beverages", "prices": {"Amazon": 285, "Flipkart": 279, "BigBasket": 269, "Blinkit": 275, "Zepto": 272}},
        {"name": "Red Label Tea 500g", "category": "beverages", "prices": {"Amazon": 265, "Flipkart": 259, "BigBasket": 249, "Blinkit": 255, "Zepto": 252}},
        {"name": "Brooke Bond Taj Mahal Tea 500g", "category": "beverages", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
        {"name": "Wagh Bakri Premium Tea 500g", "category": "beverages", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],
    "coffee": [
        {"name": "Nescafe Classic Instant Coffee 200g", "category": "beverages", "prices": {"Amazon": 499, "Flipkart": 489, "BigBasket": 479, "Blinkit": 485, "Zepto": 482}},
        {"name": "Bru Instant Coffee 200g", "category": "beverages", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 379, "Blinkit": 385, "Zepto": 382}},
        {"name": "Nescafe Gold Blend 100g", "category": "beverages", "prices": {"Amazon": 549, "Flipkart": 539, "BigBasket": 529, "Blinkit": 535, "Zepto": 532}},
        {"name": "Continental Speciale Coffee 200g", "category": "beverages", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 435, "Zepto": 432}},
    ],
    "juice": [
        {"name": "Real Fruit Power Mixed Fruit 1L", "category": "beverages", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
        {"name": "Tropicana Orange Juice 1L", "category": "beverages", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
        {"name": "Paper Boat Aam Panna 200ml (Pack of 6)", "category": "beverages", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Real Fruit Power Guava 1L", "category": "beverages", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
    ],
    "soft drinks": [
        {"name": "Coca-Cola 750ml", "category": "beverages", "prices": {"Amazon": 38, "Flipkart": 38, "BigBasket": 35, "Blinkit": 38, "Zepto": 38}},
        {"name": "Pepsi 750ml", "category": "beverages", "prices": {"Amazon": 38, "Flipkart": 38, "BigBasket": 35, "Blinkit": 38, "Zepto": 38}},
        {"name": "Sprite 750ml", "category": "beverages", "prices": {"Amazon": 38, "Flipkart": 38, "BigBasket": 35, "Blinkit": 38, "Zepto": 38}},
        {"name": "Thums Up 750ml", "category": "beverages", "prices": {"Amazon": 38, "Flipkart": 38, "BigBasket": 35, "Blinkit": 38, "Zepto": 38}},
    ],
    "water": [
        {"name": "Bisleri Mineral Water 1L (Pack of 12)", "category": "beverages", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Kinley Water 1L", "category": "beverages", "prices": {"Amazon": 20, "BigBasket": 18, "Blinkit": 20, "Zepto": 20}},
        {"name": "Himalayan Natural Mineral Water 1L", "category": "beverages", "prices": {"Amazon": 25, "BigBasket": 22, "Blinkit": 25, "Zepto": 25}},
    ],
    "health drinks": [
        {"name": "Horlicks Health Drink 500g", "category": "beverages", "prices": {"Amazon": 279, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
        {"name": "Cadbury Bournvita 500g", "category": "beverages", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Complan Royale Chocolate 500g", "category": "beverages", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Boost Health Drink 500g", "category": "beverages", "prices": {"Amazon": 259, "Flipkart": 249, "BigBasket": 239, "Blinkit": 245, "Zepto": 242}},
    ],
    "horlicks": [
        {"name": "Horlicks Health Drink 500g", "category": "beverages", "prices": {"Amazon": 279, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
    ],
    "bournvita": [
        {"name": "Cadbury Bournvita 500g", "category": "beverages", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],

    # ── Personal Care ───────────────────────────────────────────────────
    "soap": [
        {"name": "Dettol Original Soap 125g (Pack of 4)", "category": "personal_care", "prices": {"Amazon": 199, "Flipkart": 195, "BigBasket": 189, "Blinkit": 192, "Zepto": 190}},
        {"name": "Dove Cream Beauty Bar 100g", "category": "personal_care", "prices": {"Amazon": 62, "Flipkart": 59, "BigBasket": 57, "Blinkit": 58, "Zepto": 57}},
        {"name": "Lux Soft Touch Soap 150g (Pack of 4)", "category": "personal_care", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Lifebuoy Total 10 Soap 125g (Pack of 4)", "category": "personal_care", "prices": {"Amazon": 159, "Flipkart": 149, "BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
    ],
    "shampoo": [
        {"name": "Head & Shoulders Anti Dandruff Shampoo 340ml", "category": "personal_care", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Dove Hair Fall Rescue Shampoo 340ml", "category": "personal_care", "prices": {"Amazon": 289, "Flipkart": 279, "BigBasket": 269, "Blinkit": 275, "Zepto": 272}},
        {"name": "Pantene Advanced Hair Fall Solution 340ml", "category": "personal_care", "prices": {"Amazon": 279, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
        {"name": "Clinic Plus Strong & Long Shampoo 340ml", "category": "personal_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "toothpaste": [
        {"name": "Colgate MaxFresh Toothpaste 150g", "category": "personal_care", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Pepsodent Germicheck Toothpaste 200g", "category": "personal_care", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "Sensodyne Sensitive Toothpaste 150g", "category": "personal_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "face wash": [
        {"name": "Himalaya Neem Face Wash 200ml", "category": "personal_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Garnier Men Oil Clear Face Wash 100g", "category": "personal_care", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Nivea Milk Delights Face Wash 100ml", "category": "personal_care", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "deodorant": [
        {"name": "Fogg Body Spray 150ml", "category": "personal_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Wild Stone Code Platinum Deo 150ml", "category": "personal_care", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Nivea Men Fresh Active Deo 150ml", "category": "personal_care", "prices": {"Amazon": 219, "Flipkart": 209, "BigBasket": 199, "Blinkit": 205, "Zepto": 202}},
    ],
    "hair oil": [
        {"name": "Parachute Advansed Coconut Hair Oil 300ml", "category": "personal_care", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Dabur Amla Hair Oil 450ml", "category": "personal_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Bajaj Almond Drops Hair Oil 300ml", "category": "personal_care", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "body lotion": [
        {"name": "Nivea Body Lotion Nourishing 400ml", "category": "personal_care", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Vaseline Intensive Care Body Lotion 400ml", "category": "personal_care", "prices": {"Amazon": 279, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
        {"name": "Himalaya Cocoa Butter Body Lotion 400ml", "category": "personal_care", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],
    "sunscreen": [
        {"name": "Lakme Sun Expert SPF 50 100ml", "category": "personal_care", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
        {"name": "Neutrogena Ultra Sheer Sunscreen SPF 50+ 88ml", "category": "personal_care", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 569, "Blinkit": 579, "Zepto": 575}},
        {"name": "Mamaearth Ultra Light Sunscreen 80ml", "category": "personal_care", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
    ],
    "razor": [
        {"name": "Gillette Guard Razor (Pack of 3)", "category": "personal_care", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Gillette Mach3 Turbo Razor", "category": "personal_care", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 379, "Blinkit": 385, "Zepto": 382}},
        {"name": "Bombay Shaving Company Razor", "category": "personal_care", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
    ],
    "sanitary pads": [
        {"name": "Whisper Ultra Clean XL+ 30 Pads", "category": "personal_care", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Stayfree Secure XL 20 Pads", "category": "personal_care", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Sofy Antibacteria XL 28 Pads", "category": "personal_care", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
    ],

    # ── Cleaning & Household ────────────────────────────────────────────
    "detergent": [
        {"name": "Surf Excel Easy Wash Detergent Powder 1.5kg", "category": "cleaning", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 185, "Blinkit": 190, "Zepto": 187}},
        {"name": "Tide Plus Extra Power Detergent 2kg", "category": "cleaning", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 235, "Blinkit": 240, "Zepto": 237}},
        {"name": "Ariel Matic Top Load Detergent 2kg", "category": "cleaning", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 379, "Blinkit": 385, "Zepto": 382}},
    ],
    "detergent powder": [
        {"name": "Surf Excel Easy Wash Detergent Powder 1.5kg", "category": "cleaning", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 185, "Blinkit": 190, "Zepto": 187}},
    ],
    "liquid detergent": [
        {"name": "Comfort After Wash Fabric Conditioner 860ml", "category": "cleaning", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Surf Excel Matic Liquid Detergent 1L", "category": "cleaning", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Genteel Liquid Detergent 1L", "category": "cleaning", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "dishwash": [
        {"name": "Vim Dishwash Gel Lemon 500ml", "category": "cleaning", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Pril Dishwash Liquid 500ml", "category": "cleaning", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
        {"name": "Vim Dishwash Bar 500g", "category": "cleaning", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
    ],
    "floor cleaner": [
        {"name": "Lizol Disinfectant Floor Cleaner Citrus 975ml", "category": "cleaning", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Lizol Disinfectant Floor Cleaner Lavender 975ml", "category": "cleaning", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Presto! Disinfectant Floor Cleaner 2L", "category": "cleaning", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "toilet cleaner": [
        {"name": "Harpic Power Plus Toilet Cleaner 1L", "category": "cleaning", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Harpic Disinfectant Toilet Cleaner 500ml", "category": "cleaning", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "Domex Fresh Guard Toilet Cleaner 750ml", "category": "cleaning", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "glass cleaner": [
        {"name": "Colin Glass Cleaner Spray 500ml", "category": "cleaning", "prices": {"Amazon": 129, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Mr. Muscle Glass Cleaner 500ml", "category": "cleaning", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Colin Glass Cleaner Refill 1L", "category": "cleaning", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "mosquito repellent": [
        {"name": "Good Knight Gold Flash Liquid Refill (Pack of 2)", "category": "cleaning", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "All Out Ultra Liquid Refill (Pack of 2)", "category": "cleaning", "prices": {"Amazon": 139, "Flipkart": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Mortein Insta Vaporizer Refill 45ml", "category": "cleaning", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "room freshener": [
        {"name": "Odonil Room Freshener Blocks 75g (Pack of 3)", "category": "cleaning", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Ambi Pur Air Freshener Spray 275g", "category": "cleaning", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Godrej Aer Spray 240ml", "category": "cleaning", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "garbage bags": [
        {"name": "Ezee Garbage Bags Medium (Pack of 30)", "category": "cleaning", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "BB Home Garbage Bags Large (Pack of 30)", "category": "cleaning", "prices": {"BigBasket": 79, "Blinkit": 85, "Zepto": 82}},
        {"name": "Presto! Oxo-Biodegradable Garbage Bags (Pack of 30)", "category": "cleaning", "prices": {"Amazon": 119, "Flipkart": 109, "BigBasket": 99, "Blinkit": 105, "Zepto": 102}},
    ],
    "tissue paper": [
        {"name": "Origami So Soft Tissue Roll (Pack of 4)", "category": "cleaning", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Presto! Facial Tissue Box 200 Pulls", "category": "cleaning", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Kleenex Facial Tissue 100 Pulls", "category": "cleaning", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "aluminium foil": [
        {"name": "Freshwrapp Aluminium Foil 9m", "category": "cleaning", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Hindalco Aluminium Foil 72m", "category": "cleaning", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "BB Home Aluminium Foil 18m", "category": "cleaning", "prices": {"BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
    ],
    "cling wrap": [
        {"name": "Freshwrapp Cling Film 30m", "category": "cleaning", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Sanita Cling Film 100m", "category": "cleaning", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "BB Home Cling Wrap 30m", "category": "cleaning", "prices": {"BigBasket": 79, "Blinkit": 85, "Zepto": 82}},
    ],

    # ── Baby Care ───────────────────────────────────────────────────────
    "diapers": [
        {"name": "Pampers All Round Protection Pants (M) 76 Count", "category": "baby_care", "prices": {"Amazon": 999, "Flipkart": 979, "BigBasket": 959, "Blinkit": 975, "Zepto": 969}},
        {"name": "MamyPoko Pants Extra Absorb (L) 62 Count", "category": "baby_care", "prices": {"Amazon": 949, "Flipkart": 929, "BigBasket": 909, "Blinkit": 925, "Zepto": 919}},
        {"name": "Huggies Wonder Pants (M) 76 Count", "category": "baby_care", "prices": {"Amazon": 979, "Flipkart": 959, "BigBasket": 939, "Blinkit": 955, "Zepto": 949}},
    ],
    "baby food": [
        {"name": "Cerelac Baby Cereal Wheat 300g", "category": "baby_care", "prices": {"Amazon": 225, "Flipkart": 219, "BigBasket": 209, "Blinkit": 215, "Zepto": 212}},
        {"name": "Nestle Nestum Baby Cereal 300g", "category": "baby_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Cerelac Baby Cereal Rice 300g", "category": "baby_care", "prices": {"Amazon": 225, "Flipkart": 219, "BigBasket": 209, "Blinkit": 215, "Zepto": 212}},
    ],
    "baby wipes": [
        {"name": "Himalaya Gentle Baby Wipes 72 Count", "category": "baby_care", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "MamyPoko Baby Wipes 80 Count", "category": "baby_care", "prices": {"Amazon": 139, "Flipkart": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Johnson's Baby Wipes 80 Count", "category": "baby_care", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "baby soap": [
        {"name": "Johnson's Baby Soap 100g (Pack of 3)", "category": "baby_care", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Himalaya Baby Soap 125g (Pack of 3)", "category": "baby_care", "prices": {"Amazon": 129, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Sebamed Baby Cleansing Bar 100g", "category": "baby_care", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
    ],
    "baby oil": [
        {"name": "Johnson's Baby Oil 200ml", "category": "baby_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Himalaya Baby Massage Oil 200ml", "category": "baby_care", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Dabur Lal Tail 200ml", "category": "baby_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "baby powder": [
        {"name": "Johnson's Baby Powder 400g", "category": "baby_care", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 229, "Blinkit": 235, "Zepto": 232}},
        {"name": "Himalaya Baby Powder 400g", "category": "baby_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Sebamed Baby Powder 200g", "category": "baby_care", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 335, "Zepto": 332}},
    ],

    # ── Frozen & Ready to Eat ───────────────────────────────────────────
    "frozen peas": [
        {"name": "Safal Frozen Green Peas 500g", "category": "frozen", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "McCain Frozen Green Peas 1kg", "category": "frozen", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Mother Dairy Frozen Peas 500g", "category": "frozen", "prices": {"BigBasket": 75, "Blinkit": 79, "Zepto": 77}},
    ],
    "frozen parathas": [
        {"name": "McCain Aloo Tikki Paratha 400g (4 pcs)", "category": "frozen", "prices": {"Amazon": 125, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Haldiram's Frozen Lachha Paratha 400g", "category": "frozen", "prices": {"Amazon": 135, "Flipkart": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "McCain Cheese Corn Paratha 400g", "category": "frozen", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "frozen momos": [
        {"name": "Prasuma Chicken Momos 10 pcs", "category": "frozen", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Wow! Momos Veg Momos 10 pcs", "category": "frozen", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "ITC Master Chef Veg Momos 8 pcs", "category": "frozen", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "ice cream": [
        {"name": "Amul Vanilla Ice Cream 750ml", "category": "frozen", "prices": {"Amazon": 199, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Kwality Wall's Magnum Classic 80ml", "category": "frozen", "prices": {"Amazon": 99, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Baskin Robbins Pralines & Cream 500ml", "category": "frozen", "prices": {"Amazon": 349, "BigBasket": 329, "Blinkit": 339, "Zepto": 335}},
    ],
    "maggi": [
        {"name": "Maggi 2-Minute Noodles Masala (Pack of 12)", "category": "frozen", "prices": {"Amazon": 168, "Flipkart": 162, "BigBasket": 156, "Blinkit": 160, "Zepto": 158}},
        {"name": "Maggi 2-Minute Noodles Masala (Pack of 4)", "category": "frozen", "prices": {"Amazon": 56, "Flipkart": 52, "BigBasket": 48, "Blinkit": 50, "Zepto": 49}},
        {"name": "Maggi Hot Heads Barbeque Pepper 71g", "category": "frozen", "prices": {"Amazon": 25, "Flipkart": 25, "BigBasket": 22, "Blinkit": 24, "Zepto": 23}},
    ],
    "instant noodles": [
        {"name": "Maggi 2-Minute Noodles Masala (Pack of 12)", "category": "frozen", "prices": {"Amazon": 168, "Flipkart": 162, "BigBasket": 156, "Blinkit": 160, "Zepto": 158}},
        {"name": "Yippee Noodles Magic Masala (Pack of 12)", "category": "frozen", "prices": {"Amazon": 156, "Flipkart": 149, "BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
        {"name": "Top Ramen Curry Noodles (Pack of 12)", "category": "frozen", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],
    "ready to eat": [
        {"name": "MTR Ready to Eat Rajma Masala 300g", "category": "frozen", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
        {"name": "Haldiram's Ready to Eat Dal Makhani 300g", "category": "frozen", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "MTR Ready to Eat Paneer Butter Masala 300g", "category": "frozen", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "frozen chicken": [
        {"name": "Licious Chicken Breast Boneless 500g", "category": "frozen", "prices": {"BigBasket": 249, "Blinkit": 259, "Zepto": 255}},
        {"name": "FreshToHome Chicken Curry Cut 500g", "category": "frozen", "prices": {"BigBasket": 179, "Blinkit": 189, "Zepto": 185}},
        {"name": "ITC Master Chef Chicken Nuggets 450g", "category": "frozen", "prices": {"Amazon": 299, "BigBasket": 279, "Blinkit": 289, "Zepto": 285}},
    ],
    "bread": [
        {"name": "Britannia Bread White 400g", "category": "frozen", "prices": {"BigBasket": 40, "Blinkit": 38, "Zepto": 38}},
        {"name": "Harvest Gold Bread 450g", "category": "frozen", "prices": {"BigBasket": 45, "Blinkit": 42, "Zepto": 43}},
        {"name": "Britannia Brown Bread 400g", "category": "frozen", "prices": {"BigBasket": 45, "Blinkit": 42, "Zepto": 43}},
    ],

    # ── Pet Care ────────────────────────────────────────────────────────
    "dog food": [
        {"name": "Pedigree Adult Dry Dog Food Chicken & Vegetables 3kg", "category": "pet_care", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 569, "Blinkit": 585, "Zepto": 575}},
        {"name": "Royal Canin Maxi Adult Dog Food 4kg", "category": "pet_care", "prices": {"Amazon": 2499, "Flipkart": 2449, "BigBasket": 2399, "Blinkit": 2449, "Zepto": 2429}},
        {"name": "Drools Chicken & Egg Adult Dog Food 3kg", "category": "pet_care", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 439, "Zepto": 435}},
    ],
    "cat food": [
        {"name": "Whiskas Adult Cat Food Tuna 1.2kg", "category": "pet_care", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 439, "Zepto": 435}},
        {"name": "Royal Canin Indoor Cat Food 2kg", "category": "pet_care", "prices": {"Amazon": 1799, "Flipkart": 1749, "BigBasket": 1699, "Blinkit": 1749, "Zepto": 1729}},
        {"name": "Me-O Tuna Adult Cat Food 1.2kg", "category": "pet_care", "prices": {"Amazon": 349, "Flipkart": 339, "BigBasket": 329, "Blinkit": 339, "Zepto": 335}},
    ],
    "pet treats": [
        {"name": "Pedigree Dentastix Dog Treats (Pack of 7)", "category": "pet_care", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Drools Chicken Sticks Dog Treats 100g", "category": "pet_care", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
        {"name": "Temptations Cat Treats 85g", "category": "pet_care", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
}



PLATFORM_DELIVERY = {
    "Amazon": "1-3 days",
    "Flipkart": "2-4 days",
    "BigBasket": "2-4 hours",
    "Blinkit": "10-15 min",
    "Zepto": "10-15 min",
    "JioMart": "Same day",
}

PLATFORM_URLS = {
    "Amazon": "https://www.amazon.in/s?k=",
    "Flipkart": "https://www.flipkart.com/search?q=",
    "BigBasket": "https://www.bigbasket.com/ps/?q=",
    "Blinkit": "https://blinkit.com/s/?q=",
    "Zepto": "https://www.zeptonow.com/search?query=",
    "JioMart": "https://www.jiomart.com/search/",
}


# ---------------------------------------------------------------------------
# Category & suggest helpers
# ---------------------------------------------------------------------------

def get_categories() -> list[dict]:
    """Return all categories with product counts."""
    cat_counts: dict[str, int] = {}
    for _key, products in PRICE_DB.items():
        for product in products:
            cat = product.get("category", "")
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

    result = []
    for cat_id, meta in CATEGORIES.items():
        count = cat_counts.get(cat_id, 0)
        if count > 0:
            result.append({
                "id": cat_id,
                "label": meta["label"],
                "icon": meta["icon"],
                "product_count": count,
            })
    return result


def get_category_products(category_id: str) -> list[dict]:
    """Return all products in a given category."""
    products = []
    seen: set[str] = set()
    for _key, items in PRICE_DB.items():
        for item in items:
            if item.get("category") == category_id and item["name"] not in seen:
                seen.add(item["name"])
                products.append(item)
    return products


def get_suggestions(query: str, limit: int = 8) -> list[dict]:
    """Return product name suggestions matching a partial query.

    Prioritizes: starts-with matches first, then contains matches.
    """
    q = query.lower().strip()
    if not q:
        return []

    starts_with: list[dict] = []
    contains: list[dict] = []
    seen: set[str] = set()

    def _make_entry(display_name: str, category: str) -> dict:
        cat_meta = CATEGORIES.get(category, {})
        return {
            "name": display_name,
            "category": cat_meta.get("label", ""),
            "icon": cat_meta.get("icon", "🛒"),
        }

    # Pass 1: category keys
    for key in PRICE_DB:
        if key in seen:
            continue
        cat = PRICE_DB[key][0].get("category", "") if PRICE_DB[key] else ""
        if key.startswith(q):
            seen.add(key)
            starts_with.append(_make_entry(key.title(), cat))
        elif q in key:
            seen.add(key)
            contains.append(_make_entry(key.title(), cat))

    # Pass 2: product names
    for _key, products in PRICE_DB.items():
        for product in products:
            name = product["name"]
            if name in seen:
                continue
            name_lower = name.lower()
            cat = product.get("category", "")
            # Check if any word in the name starts with the query
            words = name_lower.split()
            if any(w.startswith(q) for w in words):
                seen.add(name)
                starts_with.append(_make_entry(name, cat))
            elif q in name_lower:
                seen.add(name)
                contains.append(_make_entry(name, cat))

    # Merge: starts-with first, then contains, capped at limit
    result = starts_with + contains
    return result[:limit]


def get_quantity_suggestions(query: str) -> list[str]:
    """Return quantity suggestions based on the product category."""
    q = query.lower().strip()
    # Find the category for this query
    for key, products in PRICE_DB.items():
        if q in key or key in q:
            if products:
                cat = products[0].get("category", "")
                return CATEGORY_QUANTITIES.get(cat, ["500g", "1kg", "2kg"])
    # Fallback: check product names
    for _key, products in PRICE_DB.items():
        for product in products:
            if q in product["name"].lower():
                cat = product.get("category", "")
                return CATEGORY_QUANTITIES.get(cat, ["500g", "1kg", "2kg"])
    return ["250g", "500g", "1kg", "2kg", "5kg"]


def _find_matching_products(query: str) -> list[dict]:
    """Find products matching the search query from the price database.

    Uses strict matching only — no fuzzy fallback.
    Strategy 1: Exact category key match (bidirectional substring).
    Strategy 2: Product name contains the query string.
    If nothing matches, returns empty list.
    """
    query_lower = query.lower().strip()
    matches: list[dict] = []

    # Strategy 1 — category key match (exact or multi-word prefix)
    for key, products in PRICE_DB.items():
        if key == query_lower:
            matches.extend(products)
        elif query_lower.startswith(key + " ") or key.startswith(query_lower + " "):
            matches.extend(products)

    # Strategy 2 — product name substring match (only if strategy 1 found nothing)
    if not matches:
        for _key, products in PRICE_DB.items():
            for product in products:
                if query_lower in product["name"].lower():
                    matches.append(product)

    # Deduplicate by product name
    seen: set[str] = set()
    unique: list[dict] = []
    for m in matches:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique.append(m)
    return unique


async def search_all_platforms(query: str, quantity: str = "") -> dict:
    """Search for products across all platforms."""
    search_term = f"{query} {quantity}".strip()
    matching_products = _find_matching_products(search_term)

    if not matching_products:
        matching_products = _find_matching_products(query)

    platform_results: dict[str, list[dict]] = {}
    cheapest = None
    cheapest_price = float("inf")

    all_platforms: set[str] = set()
    for product in matching_products:
        for platform in product["prices"]:
            all_platforms.add(platform)

    for platform in sorted(all_platforms):
        items = []
        for product in matching_products:
            price = product["prices"].get(platform)
            if price is None:
                continue

            search_url = PLATFORM_URLS.get(platform, "")
            product_url = f"{search_url}{query.replace(' ', '+')}" if search_url else ""

            item = {
                "name": product["name"],
                "price": price,
                "platform": platform,
                "product_url": product_url,
                "image_url": "",
                "delivery_time": PLATFORM_DELIVERY.get(platform, "N/A"),
                "in_stock": True,
                "rating": 4.2,
                "original_price": round(price * 1.1, 2),
                "discount_pct": round(10.0, 1),
                "unit": "",
                "quantity": quantity,
            }
            items.append(item)

            if price < cheapest_price:
                cheapest_price = price
                cheapest = item

        platform_results[platform] = items

    return {
        "query": query,
        "quantity": quantity,
        "platforms": platform_results,
        "cheapest": cheapest,
        "platform_count": len(platform_results),
        "total_results": sum(len(v) for v in platform_results.values()),
    }


def _build_summary(results: list[dict]) -> dict:
    """Build a consolidated summary for list comparison results."""
    all_platforms = set()
    for comp in results:
        for p in comp.get("platforms", {}):
            all_platforms.add(p)

    platform_totals: dict[str, float] = {p: 0.0 for p in sorted(all_platforms)}
    cheapest_cart: list[dict] = []
    total_cheapest_cost = 0.0
    items_found = 0

    for comp in results:
        if not comp.get("cheapest"):
            continue
        items_found += 1
        c = comp["cheapest"]
        cheapest_cart.append({
            "item": c["name"],
            "platform": c["platform"],
            "price": c["price"],
        })
        total_cheapest_cost += c["price"]

        for platform in all_platforms:
            platform_items = comp.get("platforms", {}).get(platform, [])
            if platform_items:
                min_price = min(item["price"] for item in platform_items)
                platform_totals[platform] += min_price

    best_platform = ""
    best_platform_cost = float("inf")
    for p, total in platform_totals.items():
        if total > 0 and total < best_platform_cost:
            best_platform_cost = total
            best_platform = p

    max_platform_cost = max((t for t in platform_totals.values() if t > 0), default=0)
    savings = round(max_platform_cost - total_cheapest_cost, 2) if max_platform_cost > 0 else 0

    summary = {
        "total_items": items_found,
        "total_cheapest_cost": round(total_cheapest_cost, 2),
        "savings_vs_most_expensive": savings,
        "best_platform": best_platform,
        "cheapest_cart": cheapest_cart,
    }

    for p in sorted(all_platforms):
        key = f"total_{p.lower().replace(' ', '_')}_cost"
        summary[key] = round(platform_totals[p], 2)

    return summary


async def search_list(items: list[dict]) -> tuple[list[dict], dict]:
    """Compare prices for a list of items. Returns (results, summary)."""
    results = []
    for item in items:
        query = item.get("name", "")
        qty = item.get("quantity", "")
        if query:
            comparison = await search_all_platforms(query, qty)
            results.append(comparison)

    summary = _build_summary(results)
    return results, summary
