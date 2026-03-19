import os
from datetime import datetime
from typing import Optional
import json

USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true"
MONGODB_URL = os.getenv("MONGODB_URL", "")

# In-memory store for demo/development when no DB is configured
_store = {
    "users": {},
    "products": {},
    "orders": {},
    "cart": {}
}

def _new_id():
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:24]

# ── Seed demo data ──────────────────────────────────────────────
def seed_demo_data():
    from utils.security import get_password_hash
    if not _store["users"]:
        _store["users"]["demo_user_id"] = {
            "_id": "demo_user_id",
            "name": "Demo User",
            "email": "user@demo.com",
            "hashed_password": get_password_hash("demo1234"),
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
            "address": {}
        }
        _store["users"]["admin_user_id"] = {
            "_id": "admin_user_id",
            "name": "Admin",
            "email": "admin@demo.com",
            "hashed_password": get_password_hash("admin1234"),
            "role": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "address": {}
        }

    if not _store["products"]:
        products = [
            {"name": "Wireless Noise-Cancelling Headphones", "price": 299.99, "category": "Electronics", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop", "description": "Premium over-ear headphones with 30hr battery life and spatial audio.", "stock": 50, "rating": 4.8},
            {"name": "Minimalist Leather Watch", "price": 189.00, "category": "Accessories", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop", "description": "Swiss movement, sapphire crystal, genuine Italian leather strap.", "stock": 30, "rating": 4.9},
            {"name": "Ultralight Running Shoes", "price": 149.95, "category": "Footwear", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop", "description": "Carbon-fibre plate, responsive foam, 198g per shoe.", "stock": 80, "rating": 4.7},
            {"name": "Ceramic Pour-Over Coffee Set", "price": 64.00, "category": "Home", "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=400&fit=crop", "description": "Handcrafted ceramic dripper, server & two mugs.", "stock": 40, "rating": 4.6},
            {"name": "Mechanical Keyboard TKL", "price": 229.00, "category": "Electronics", "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=400&fit=crop", "description": "Cherry MX Brown switches, aircraft-grade aluminium body.", "stock": 25, "rating": 4.8},
            {"name": "Canvas Backpack 26L", "price": 89.00, "category": "Bags", "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop", "description": "Waxed canvas, vegetable-tanned leather trim, fits 15\" laptop.", "stock": 60, "rating": 4.5},
            {"name": "Stainless Steel Water Bottle", "price": 39.95, "category": "Home", "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&h=400&fit=crop", "description": "Triple-wall vacuum insulation, 24 hr cold / 12 hr hot.", "stock": 100, "rating": 4.7},
            {"name": "Merino Wool Crew Sweater", "price": 119.00, "category": "Clothing", "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=400&fit=crop", "description": "100% superfine merino, ethically sourced, available in 8 colours.", "stock": 45, "rating": 4.6},
        ]
        for p in products:
            pid = _new_id()
            p["_id"] = pid
            p["created_at"] = datetime.utcnow().isoformat()
            _store["products"][pid] = p

# ── Generic DB interface (in-memory) ───────────────────────────
class MemoryDB:
    def __init__(self, collection: str):
        self.col = collection

    async def find_one(self, query: dict):
        for doc in _store[self.col].values():
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    async def find(self, query: dict = None, sort=None, skip=0, limit=100):
        results = list(_store[self.col].values())
        if query:
            results = [d for d in results if all(d.get(k) == v for k, v in query.items())]
        if sort:
            key, direction = sort[0]
            results.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
        return results[skip:skip+limit]

    async def insert_one(self, doc: dict):
        doc_id = _new_id()
        doc["_id"] = doc_id
        doc["created_at"] = datetime.utcnow().isoformat()
        _store[self.col][doc_id] = doc
        return doc_id

    async def update_one(self, query: dict, update: dict):
        for doc_id, doc in _store[self.col].items():
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                _store[self.col][doc_id] = doc
                return True
        return False

    async def count(self, query: dict = None):
        docs = await self.find(query)
        return len(docs)

    async def delete_one(self, query: dict):
        for doc_id, doc in list(_store[self.col].items()):
            if all(doc.get(k) == v for k, v in query.items()):
                del _store[self.col][doc_id]
                return True
        return False

def get_collection(name: str) -> MemoryDB:
    if name not in _store:
        _store[name] = {}
    return MemoryDB(name)
