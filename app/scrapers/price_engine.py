"""Unified price engine using a curated price database.

Provides price comparison across Indian e-commerce platforms
with strict matching logic and consolidated summary support.
"""

from __future__ import annotations

import logging

from .base import ProductResult

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated grocery price database — realistic Indian prices across platforms
# ---------------------------------------------------------------------------
PRICE_DB = {
    # ── Fruits ──────────────────────────────────────────────────────────
    "apple": [
        {"name": "Shimla Apple 1kg", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 175, "Blinkit": 180, "Zepto": 178}},
        {"name": "Kinnaur Apple Premium 1kg", "prices": {"Amazon": 280, "Flipkart": 269, "BigBasket": 259, "Blinkit": 265, "Zepto": 262}},
    ],
    "banana": [
        {"name": "Robusta Banana (1 Dozen)", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 40, "Blinkit": 42, "Zepto": 41}},
        {"name": "Elaichi Banana (500g)", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "papaya": [
        {"name": "Fresh Papaya 1kg", "prices": {"BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
        {"name": "Semi-Ripe Papaya 1pc (~800g)", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
    ],
    "mango": [
        {"name": "Alphonso Mango (Hapus) 1kg", "prices": {"Amazon": 699, "Flipkart": 679, "BigBasket": 649, "Blinkit": 669, "Zepto": 659}},
        {"name": "Kesar Mango 1kg", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 369, "Blinkit": 379, "Zepto": 375}},
    ],
    "orange": [
        {"name": "Nagpur Orange 1kg", "prices": {"Amazon": 129, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Imported Malta Orange 1kg", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "grapes": [
        {"name": "Green Seedless Grapes 500g", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 85, "Blinkit": 89, "Zepto": 87}},
        {"name": "Black Grapes 500g", "prices": {"BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "watermelon": [
        {"name": "Watermelon 1pc (~2-3kg)", "prices": {"BigBasket": 59, "Blinkit": 55, "Zepto": 57}},
    ],
    "pomegranate": [
        {"name": "Pomegranate (Anar) 500g", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 125, "Blinkit": 130, "Zepto": 128}},
    ],
    "guava": [
        {"name": "Fresh Guava (Amrood) 500g", "prices": {"BigBasket": 45, "Blinkit": 48, "Zepto": 46}},
    ],
    "kiwi": [
        {"name": "Zespri Green Kiwi (3 pcs)", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 155, "Blinkit": 162, "Zepto": 158}},
    ],

    # ── Vegetables ──────────────────────────────────────────────────────
    "potato": [
        {"name": "Fresh Potato (Aloo) 1kg", "prices": {"Amazon": 39, "Flipkart": 35, "BigBasket": 30, "Blinkit": 32, "Zepto": 31}},
    ],
    "onion": [
        {"name": "Onion (Pyaaz) 1kg", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "tomato": [
        {"name": "Tomato (Tamatar) 1kg", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 38, "Blinkit": 40, "Zepto": 39}},
        {"name": "Hybrid Tomato 500g", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
    ],
    "carrot": [
        {"name": "Fresh Carrot (Gajar) 500g", "prices": {"Amazon": 39, "Flipkart": 35, "BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
    ],
    "capsicum": [
        {"name": "Green Capsicum (Shimla Mirch) 250g", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "brinjal": [
        {"name": "Brinjal (Baingan) 500g", "prices": {"BigBasket": 29, "Blinkit": 32, "Zepto": 30}},
    ],
    "cauliflower": [
        {"name": "Cauliflower (Phool Gobi) 1pc", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "cabbage": [
        {"name": "Cabbage (Patta Gobi) 1pc (~500g)", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
    ],
    "spinach": [
        {"name": "Spinach (Palak) 250g", "prices": {"BigBasket": 22, "Blinkit": 25, "Zepto": 23}},
    ],
    "peas": [
        {"name": "Green Peas (Matar) 250g", "prices": {"BigBasket": 35, "Blinkit": 38, "Zepto": 36}},
    ],
    "beans": [
        {"name": "French Beans 250g", "prices": {"BigBasket": 32, "Blinkit": 35, "Zepto": 33}},
    ],
    "lady finger": [
        {"name": "Lady Finger (Bhindi) 250g", "prices": {"BigBasket": 28, "Blinkit": 30, "Zepto": 29}},
    ],
    "cucumber": [
        {"name": "Cucumber (Kheera) 500g", "prices": {"BigBasket": 25, "Blinkit": 28, "Zepto": 26}},
    ],
    "ginger": [
        {"name": "Fresh Ginger (Adrak) 100g", "prices": {"BigBasket": 19, "Blinkit": 22, "Zepto": 20}},
    ],
    "garlic": [
        {"name": "Garlic (Lahsun) 250g", "prices": {"Amazon": 55, "Flipkart": 49, "BigBasket": 42, "Blinkit": 45, "Zepto": 43}},
    ],

    # ── Dairy ───────────────────────────────────────────────────────────
    "milk": [
        {"name": "Amul Taaza Toned Milk 1L", "prices": {"Amazon": 66, "BigBasket": 62, "Blinkit": 62, "Zepto": 62}},
        {"name": "Mother Dairy Full Cream Milk 1L", "prices": {"BigBasket": 68, "Blinkit": 68, "Zepto": 68}},
    ],
    "ghee": [
        {"name": "Amul Pure Ghee 1L", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 565, "Blinkit": 575, "Zepto": 570}},
        {"name": "Patanjali Cow Ghee 1L", "prices": {"Amazon": 549, "Flipkart": 539, "BigBasket": 525, "Blinkit": 535, "Zepto": 530}},
    ],
    "cheese": [
        {"name": "Amul Cheese Slices 200g (10 Slices)", "prices": {"Amazon": 120, "Flipkart": 115, "BigBasket": 105, "Blinkit": 110, "Zepto": 108}},
        {"name": "Britannia Cheese Block 200g", "prices": {"Amazon": 110, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
    ],
    "curd": [
        {"name": "Amul Masti Dahi 400g", "prices": {"BigBasket": 35, "Blinkit": 33, "Zepto": 33}},
        {"name": "Mother Dairy Classic Curd 400g", "prices": {"BigBasket": 32, "Blinkit": 30, "Zepto": 30}},
    ],
    "yogurt": [
        {"name": "Epigamia Greek Yogurt 90g", "prices": {"Amazon": 55, "BigBasket": 49, "Blinkit": 50, "Zepto": 49}},
        {"name": "Amul Misti Doi 400g", "prices": {"BigBasket": 55, "Blinkit": 52, "Zepto": 53}},
    ],
    "buttermilk": [
        {"name": "Amul Masti Buttermilk 200ml", "prices": {"BigBasket": 15, "Blinkit": 15, "Zepto": 15}},
        {"name": "Mother Dairy Chaach 500ml", "prices": {"BigBasket": 25, "Blinkit": 25, "Zepto": 25}},
    ],
    "cream": [
        {"name": "Amul Fresh Cream 200ml", "prices": {"Amazon": 65, "BigBasket": 55, "Blinkit": 58, "Zepto": 56}},
    ],
    "butter": [
        {"name": "Amul Butter 500g", "prices": {"Amazon": 275, "Flipkart": 270, "BigBasket": 265, "Blinkit": 268, "Zepto": 267}},
        {"name": "Amul Butter 100g", "prices": {"Amazon": 57, "Flipkart": 56, "BigBasket": 54, "Blinkit": 55, "Zepto": 54}},
    ],
    "paneer": [
        {"name": "Amul Fresh Paneer 200g", "prices": {"Amazon": 95, "BigBasket": 85, "Blinkit": 88, "Zepto": 86}},
        {"name": "Mother Dairy Paneer 200g", "prices": {"BigBasket": 80, "Blinkit": 82, "Zepto": 80}},
    ],
    "eggs": [
        {"name": "Farm Fresh White Eggs (Pack of 12)", "prices": {"BigBasket": 79, "Blinkit": 75, "Zepto": 76}},
        {"name": "Country Eggs Brown (Pack of 6)", "prices": {"BigBasket": 65, "Blinkit": 62, "Zepto": 63}},
    ],

    # ── Staples ─────────────────────────────────────────────────────────
    "toor dal": [
        {"name": "Tata Sampann Toor Dal 1kg", "prices": {"Amazon": 179, "Flipkart": 175, "BigBasket": 169, "Blinkit": 172, "Zepto": 170}},
        {"name": "Fortune Arhar Dal (Toor) 1kg", "prices": {"Amazon": 165, "Flipkart": 162, "BigBasket": 159, "Blinkit": 164, "Zepto": 160}},
        {"name": "BB Royal Toor Dal 1kg", "prices": {"BigBasket": 145, "Blinkit": 150, "Zepto": 148}},
    ],
    "moong dal": [
        {"name": "Tata Sampann Moong Dal 1kg", "prices": {"Amazon": 169, "Flipkart": 165, "BigBasket": 159, "Blinkit": 162, "Zepto": 160}},
        {"name": "BB Royal Moong Dal 1kg", "prices": {"BigBasket": 139, "Blinkit": 145, "Zepto": 142}},
    ],
    "chana dal": [
        {"name": "Tata Sampann Chana Dal 1kg", "prices": {"Amazon": 139, "Flipkart": 135, "BigBasket": 129, "Blinkit": 132, "Zepto": 130}},
    ],
    "urad dal": [
        {"name": "Tata Sampann Urad Dal 1kg", "prices": {"Amazon": 189, "Flipkart": 185, "BigBasket": 179, "Blinkit": 182, "Zepto": 180}},
    ],
    "rajma": [
        {"name": "Tata Sampann Rajma 500g", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
        {"name": "BB Royal Rajma Chitra 1kg", "prices": {"Amazon": 189, "Flipkart": 179, "BigBasket": 169, "Blinkit": 175, "Zepto": 172}},
    ],
    "chole": [
        {"name": "Tata Sampann Kabuli Chana 500g", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "chickpeas": [
        {"name": "Tata Sampann Kabuli Chana 500g", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "rice": [
        {"name": "India Gate Basmati Rice 5kg", "prices": {"Amazon": 599, "Flipkart": 579, "BigBasket": 569, "Blinkit": 589, "Zepto": 575}},
        {"name": "Daawat Rozana Basmati Rice 5kg", "prices": {"Amazon": 449, "Flipkart": 439, "BigBasket": 429, "Blinkit": 445, "Zepto": 435}},
    ],
    "atta": [
        {"name": "Aashirvaad Atta 10kg", "prices": {"Amazon": 489, "Flipkart": 479, "BigBasket": 469, "Blinkit": 485, "Zepto": 475}},
        {"name": "Fortune Chakki Fresh Atta 5kg", "prices": {"Amazon": 265, "Flipkart": 259, "BigBasket": 249, "Blinkit": 255, "Zepto": 252}},
    ],
    "wheat flour": [
        {"name": "Aashirvaad Atta 10kg", "prices": {"Amazon": 489, "Flipkart": 479, "BigBasket": 469, "Blinkit": 485, "Zepto": 475}},
        {"name": "Fortune Chakki Fresh Atta 5kg", "prices": {"Amazon": 265, "Flipkart": 259, "BigBasket": 249, "Blinkit": 255, "Zepto": 252}},
    ],
    "poha": [
        {"name": "BB Royal Poha (Flattened Rice) Thick 500g", "prices": {"Amazon": 45, "Flipkart": 42, "BigBasket": 38, "Blinkit": 40, "Zepto": 39}},
    ],
    "sooji": [
        {"name": "BB Royal Sooji (Rava) 500g", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
    ],
    "rava": [
        {"name": "BB Royal Sooji (Rava) 500g", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
    ],
    "sugar": [
        {"name": "Madhur Pure Sugar 1kg", "prices": {"Amazon": 49, "Flipkart": 47, "BigBasket": 45, "Blinkit": 46, "Zepto": 45}},
        {"name": "Trust Classic Sugar 5kg", "prices": {"Amazon": 235, "Flipkart": 229, "BigBasket": 225, "Blinkit": 230, "Zepto": 228}},
    ],

    # ── Cooking ─────────────────────────────────────────────────────────
    "oil": [
        {"name": "Fortune Sunlite Refined Sunflower Oil 1L", "prices": {"Amazon": 145, "Flipkart": 139, "BigBasket": 135, "Blinkit": 140, "Zepto": 137}},
        {"name": "Saffola Gold Edible Oil 1L", "prices": {"Amazon": 189, "Flipkart": 185, "BigBasket": 179, "Blinkit": 182, "Zepto": 180}},
    ],
    "sunflower oil": [
        {"name": "Fortune Sunlite Refined Sunflower Oil 1L", "prices": {"Amazon": 145, "Flipkart": 139, "BigBasket": 135, "Blinkit": 140, "Zepto": 137}},
        {"name": "Freedom Refined Sunflower Oil 1L", "prices": {"Amazon": 135, "Flipkart": 129, "BigBasket": 125, "Blinkit": 130, "Zepto": 127}},
    ],
    "mustard oil": [
        {"name": "Fortune Kachi Ghani Mustard Oil 1L", "prices": {"Amazon": 179, "Flipkart": 175, "BigBasket": 169, "Blinkit": 172, "Zepto": 170}},
        {"name": "Patanjali Mustard Oil 1L", "prices": {"Amazon": 165, "Flipkart": 159, "BigBasket": 155, "Blinkit": 158, "Zepto": 156}},
    ],
    "olive oil": [
        {"name": "Figaro Extra Virgin Olive Oil 500ml", "prices": {"Amazon": 499, "Flipkart": 479, "BigBasket": 465, "Blinkit": 475, "Zepto": 470}},
        {"name": "Borges Extra Virgin Olive Oil 500ml", "prices": {"Amazon": 549, "Flipkart": 529, "BigBasket": 515, "Blinkit": 525, "Zepto": 520}},
    ],
    "salt": [
        {"name": "Tata Salt 1kg", "prices": {"Amazon": 28, "Flipkart": 25, "BigBasket": 22, "Blinkit": 24, "Zepto": 23}},
        {"name": "Tata Rock Salt 1kg", "prices": {"Amazon": 39, "Flipkart": 36, "BigBasket": 32, "Blinkit": 34, "Zepto": 33}},
    ],
    "turmeric": [
        {"name": "MDH Turmeric Powder 100g", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 42, "Blinkit": 44, "Zepto": 43}},
        {"name": "Everest Turmeric Powder 200g", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
    ],
    "chilli powder": [
        {"name": "MDH Deggi Mirch 100g", "prices": {"Amazon": 65, "Flipkart": 62, "BigBasket": 58, "Blinkit": 60, "Zepto": 59}},
        {"name": "Everest Kashmirilal Chilli Powder 100g", "prices": {"Amazon": 75, "Flipkart": 72, "BigBasket": 68, "Blinkit": 70, "Zepto": 69}},
    ],
    "cumin": [
        {"name": "MDH Cumin (Jeera) Powder 100g", "prices": {"Amazon": 79, "Flipkart": 75, "BigBasket": 69, "Blinkit": 72, "Zepto": 70}},
        {"name": "Whole Cumin Seeds (Jeera) 200g", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
    ],
    "coriander powder": [
        {"name": "MDH Coriander Powder 100g", "prices": {"Amazon": 49, "Flipkart": 45, "BigBasket": 42, "Blinkit": 44, "Zepto": 43}},
    ],

    # ── Snacks ──────────────────────────────────────────────────────────
    "chips": [
        {"name": "Lay's Classic Salted Chips 52g", "prices": {"Amazon": 20, "Flipkart": 20, "BigBasket": 18, "Blinkit": 20, "Zepto": 20}},
        {"name": "Kurkure Masala Munch 100g", "prices": {"Amazon": 25, "Flipkart": 25, "BigBasket": 22, "Blinkit": 24, "Zepto": 23}},
    ],
    "namkeen": [
        {"name": "Haldiram's Aloo Bhujia 400g", "prices": {"Amazon": 135, "Flipkart": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
        {"name": "Haldiram's Moong Dal 400g", "prices": {"Amazon": 125, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
    ],
    "biscuit": [
        {"name": "Parle-G Gold Biscuits 1kg", "prices": {"Amazon": 115, "Flipkart": 110, "BigBasket": 105, "Blinkit": 108, "Zepto": 106}},
        {"name": "Britannia Good Day Cashew 600g", "prices": {"Amazon": 165, "Flipkart": 159, "BigBasket": 155, "Blinkit": 158, "Zepto": 156}},
    ],
    "biscuits": [
        {"name": "Parle-G Gold Biscuits 1kg", "prices": {"Amazon": 115, "Flipkart": 110, "BigBasket": 105, "Blinkit": 108, "Zepto": 106}},
        {"name": "Britannia Good Day Cashew 600g", "prices": {"Amazon": 165, "Flipkart": 159, "BigBasket": 155, "Blinkit": 158, "Zepto": 156}},
    ],
    "cookies": [
        {"name": "Britannia Good Day Choco Chip 600g", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Unibic Choco Chip Cookies 500g", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
    ],
    "chocolate": [
        {"name": "Cadbury Dairy Milk Silk 150g", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
        {"name": "Cadbury Dairy Milk 110g", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],

    # ── Beverages ───────────────────────────────────────────────────────
    "tea": [
        {"name": "Tata Tea Gold 500g", "prices": {"Amazon": 285, "Flipkart": 279, "BigBasket": 269, "Blinkit": 275, "Zepto": 272}},
        {"name": "Red Label Tea 500g", "prices": {"Amazon": 265, "Flipkart": 259, "BigBasket": 249, "Blinkit": 255, "Zepto": 252}},
    ],
    "coffee": [
        {"name": "Nescafe Classic Instant Coffee 200g", "prices": {"Amazon": 499, "Flipkart": 489, "BigBasket": 479, "Blinkit": 485, "Zepto": 482}},
        {"name": "Bru Instant Coffee 200g", "prices": {"Amazon": 399, "Flipkart": 389, "BigBasket": 379, "Blinkit": 385, "Zepto": 382}},
    ],
    "juice": [
        {"name": "Real Fruit Power Mixed Fruit 1L", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
        {"name": "Tropicana Orange Juice 1L", "prices": {"Amazon": 119, "Flipkart": 115, "BigBasket": 109, "Blinkit": 112, "Zepto": 110}},
    ],
    "soft drinks": [
        {"name": "Coca-Cola 750ml", "prices": {"Amazon": 38, "Flipkart": 38, "BigBasket": 35, "Blinkit": 38, "Zepto": 38}},
        {"name": "Thums Up 750ml", "prices": {"Amazon": 38, "Flipkart": 38, "BigBasket": 35, "Blinkit": 38, "Zepto": 38}},
    ],
    "water": [
        {"name": "Bisleri Mineral Water 1L (Pack of 12)", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Kinley Water 1L", "prices": {"Amazon": 20, "BigBasket": 18, "Blinkit": 20, "Zepto": 20}},
    ],

    # ── Personal Care ───────────────────────────────────────────────────
    "soap": [
        {"name": "Dettol Original Soap 125g (Pack of 4)", "prices": {"Amazon": 199, "Flipkart": 195, "BigBasket": 189, "Blinkit": 192, "Zepto": 190}},
        {"name": "Dove Cream Beauty Bar 100g", "prices": {"Amazon": 62, "Flipkart": 59, "BigBasket": 57, "Blinkit": 58, "Zepto": 57}},
    ],
    "shampoo": [
        {"name": "Head & Shoulders Anti Dandruff Shampoo 340ml", "prices": {"Amazon": 299, "Flipkart": 289, "BigBasket": 279, "Blinkit": 285, "Zepto": 282}},
        {"name": "Dove Hair Fall Rescue Shampoo 340ml", "prices": {"Amazon": 289, "Flipkart": 279, "BigBasket": 269, "Blinkit": 275, "Zepto": 272}},
    ],
    "toothpaste": [
        {"name": "Colgate MaxFresh Toothpaste 150g", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Pepsodent Germicheck Toothpaste 200g", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "face wash": [
        {"name": "Himalaya Neem Face Wash 200ml", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Garnier Men Oil Clear Face Wash 100g", "prices": {"Amazon": 175, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "deodorant": [
        {"name": "Fogg Body Spray 150ml", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Nivea Men Fresh Active Deo 150ml", "prices": {"Amazon": 219, "Flipkart": 209, "BigBasket": 199, "Blinkit": 205, "Zepto": 202}},
    ],

    # ── Cleaning ────────────────────────────────────────────────────────
    "detergent": [
        {"name": "Surf Excel Easy Wash Detergent Powder 1.5kg", "prices": {"Amazon": 199, "Flipkart": 189, "BigBasket": 185, "Blinkit": 190, "Zepto": 187}},
        {"name": "Tide Plus Extra Power Detergent 2kg", "prices": {"Amazon": 249, "Flipkart": 239, "BigBasket": 235, "Blinkit": 240, "Zepto": 237}},
    ],
    "dishwash": [
        {"name": "Vim Dishwash Gel Lemon 500ml", "prices": {"Amazon": 99, "Flipkart": 95, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
        {"name": "Pril Dishwash Liquid 500ml", "prices": {"Amazon": 109, "Flipkart": 105, "BigBasket": 99, "Blinkit": 102, "Zepto": 100}},
    ],
    "floor cleaner": [
        {"name": "Lizol Disinfectant Floor Cleaner Citrus 975ml", "prices": {"Amazon": 179, "Flipkart": 169, "BigBasket": 159, "Blinkit": 165, "Zepto": 162}},
    ],
    "toilet cleaner": [
        {"name": "Harpic Power Plus Toilet Cleaner 1L", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],

    # ── Baby ────────────────────────────────────────────────────────────
    "diapers": [
        {"name": "Pampers All Round Protection Pants (M) 76 Count", "prices": {"Amazon": 999, "Flipkart": 979, "BigBasket": 959, "Blinkit": 975, "Zepto": 969}},
        {"name": "MamyPoko Pants Extra Absorb (L) 62 Count", "prices": {"Amazon": 949, "Flipkart": 929, "BigBasket": 909, "Blinkit": 925, "Zepto": 919}},
    ],
    "baby food": [
        {"name": "Cerelac Baby Cereal Wheat 300g", "prices": {"Amazon": 225, "Flipkart": 219, "BigBasket": 209, "Blinkit": 215, "Zepto": 212}},
    ],
    "baby wipes": [
        {"name": "Himalaya Gentle Baby Wipes 72 Count", "prices": {"Amazon": 149, "Flipkart": 139, "BigBasket": 129, "Blinkit": 135, "Zepto": 132}},
    ],

    # ── Frozen ──────────────────────────────────────────────────────────
    "ice cream": [
        {"name": "Amul Vanilla Ice Cream 750ml", "prices": {"Amazon": 199, "BigBasket": 179, "Blinkit": 185, "Zepto": 182}},
        {"name": "Kwality Wall's Magnum Classic 80ml", "prices": {"Amazon": 99, "BigBasket": 89, "Blinkit": 92, "Zepto": 90}},
    ],
    "frozen peas": [
        {"name": "Safal Frozen Green Peas 500g", "prices": {"Amazon": 89, "Flipkart": 85, "BigBasket": 79, "Blinkit": 82, "Zepto": 80}},
    ],
    "frozen parathas": [
        {"name": "McCain Aloo Tikki Paratha 400g (4 pcs)", "prices": {"Amazon": 125, "Flipkart": 119, "BigBasket": 109, "Blinkit": 115, "Zepto": 112}},
        {"name": "Haldiram's Frozen Lachha Paratha 400g", "prices": {"Amazon": 135, "Flipkart": 129, "BigBasket": 119, "Blinkit": 125, "Zepto": 122}},
    ],

    # ── Other common items ──────────────────────────────────────────────
    "maggi": [
        {"name": "Maggi 2-Minute Noodles Masala (Pack of 12)", "prices": {"Amazon": 168, "Flipkart": 162, "BigBasket": 156, "Blinkit": 160, "Zepto": 158}},
    ],
    "bread": [
        {"name": "Britannia Bread White 400g", "prices": {"BigBasket": 40, "Blinkit": 38, "Zepto": 38}},
        {"name": "Harvest Gold Bread 450g", "prices": {"BigBasket": 45, "Blinkit": 42, "Zepto": 43}},
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
            # Only match prefix if followed by a space (word boundary)
            matches.extend(products)

    # Strategy 2 — product name substring match (only if strategy 1 found nothing)
    if not matches:
        for _key, products in PRICE_DB.items():
            for product in products:
                if query_lower in product["name"].lower():
                    matches.append(product)

    # NO fuzzy fallback — return empty if nothing matches

    # Deduplicate by product name
    seen: set[str] = set()
    unique: list[dict] = []
    for m in matches:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique.append(m)
    return unique


async def search_all_platforms(query: str, quantity: str = "") -> dict:
    """Search for products across all platforms.

    Returns a dict with platform results, cheapest item, and totals.
    """
    search_term = f"{query} {quantity}".strip()
    matching_products = _find_matching_products(search_term)

    if not matching_products:
        # Retry without quantity
        matching_products = _find_matching_products(query)

    platform_results: dict[str, list[dict]] = {}
    cheapest = None
    cheapest_price = float("inf")

    # Collect all platforms present in matched products
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

        # Sum cheapest-per-platform for each platform
        for platform in all_platforms:
            platform_items = comp.get("platforms", {}).get(platform, [])
            if platform_items:
                # Use the cheapest item on this platform for this query
                min_price = min(item["price"] for item in platform_items)
                platform_totals[platform] += min_price

    # Find best single platform (lowest total if you bought everything there)
    best_platform = ""
    best_platform_cost = float("inf")
    for p, total in platform_totals.items():
        if total > 0 and total < best_platform_cost:
            best_platform_cost = total
            best_platform = p

    # Savings vs most expensive platform
    max_platform_cost = max((t for t in platform_totals.values() if t > 0), default=0)
    savings = round(max_platform_cost - total_cheapest_cost, 2) if max_platform_cost > 0 else 0

    summary = {
        "total_items": items_found,
        "total_cheapest_cost": round(total_cheapest_cost, 2),
        "savings_vs_most_expensive": savings,
        "best_platform": best_platform,
        "cheapest_cart": cheapest_cart,
    }

    # Add per-platform totals
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
