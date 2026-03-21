import os
from datetime import datetime
from typing import Optional
import uuid
import asyncio
from google.cloud import firestore

db = firestore.AsyncClient(project="capstone-project-490610")

def _new_id():
    return str(uuid.uuid4()).replace("-", "")[:24]

class FirestoreDB:
    def __init__(self, collection: str):
        self.col = collection
        self.ref = db.collection(collection)

    async def find_one(self, query: dict):
        if "_id" in query:
            doc = await self.ref.document(query["_id"]).get()
            if doc.exists:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            return None
        q = self.ref
        for k, v in query.items():
            q = q.where(k, "==", v)
        docs = q.limit(1).stream()
        async for doc in docs:
            data = doc.to_dict()
            data["_id"] = doc.id
            return data
        return None

    async def find(self, query: dict = None, sort=None, skip=0, limit=100):
        q = self.ref
        if query:
            for k, v in query.items():
                q = q.where(k, "==", v)
        if sort:
            key, direction = sort[0]
            q = q.order_by(
                key,
                direction=firestore.Query.DESCENDING if direction == -1 else firestore.Query.ASCENDING
            )
        q = q.limit(limit)
        results = []
        async for doc in q.stream():
            data = doc.to_dict()
            data["_id"] = doc.id
            results.append(data)
        return results

    async def insert_one(self, doc: dict):
        doc_id = _new_id()
        doc["_id"] = doc_id
        doc["created_at"] = datetime.utcnow().isoformat()
        await self.ref.document(doc_id).set(doc)
        return doc_id

    async def update_one(self, query: dict, update: dict):
        if "_id" in query:
            doc_ref = self.ref.document(query["_id"])
            if "$set" in update:
                await doc_ref.update(update["$set"])
            return True
        doc = await self.find_one(query)
        if doc:
            doc_ref = self.ref.document(doc["_id"])
            if "$set" in update:
                await doc_ref.update(update["$set"])
            return True
        return False

    async def count(self, query: dict = None):
        docs = await self.find(query)
        return len(docs)

    async def delete_one(self, query: dict):
        doc = await self.find_one(query)
        if doc:
            await self.ref.document(doc["_id"]).delete()
            return True
        return False

def get_collection(name: str) -> FirestoreDB:
    return FirestoreDB(name)

def seed_demo_data():
    asyncio.create_task(_seed_async())

async def _seed_async():
    from utils.security import get_password_hash
    users = FirestoreDB("users")
    existing = await users.find_one({"email": "user@demo.com"})
    if existing:
        return

    await users.insert_one({
        "name": "Demo User",
        "email": "user@demo.com",
        "hashed_password": get_password_hash("demo1234"),
        "role": "user",
        "address": {}
    })
    await users.insert_one({
        "name": "Admin",
        "email": "admin@demo.com",
        "hashed_password": get_password_hash("admin1234"),
        "role": "admin",
        "address": {}
    })

    products = FirestoreDB("products")
    existing_products = await products.find()
    if existing_products:
        return

    items = [
        {"name": "Wireless Noise-Cancelling Headphones", "price": 299.99, "category": "Electronics", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop", "description": "Premium over-ear headphones with 30hr battery life.", "stock": 50, "rating": 4.8},
        {"name": "Minimalist Leather Watch", "price": 189.00, "category": "Accessories", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop", "description": "Swiss movement, sapphire crystal.", "stock": 30, "rating": 4.9},
        {"name": "Ultralight Running Shoes", "price": 149.95, "category": "Footwear", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop", "description": "Carbon-fibre plate, responsive foam.", "stock": 80, "rating": 4.7},
        {"name": "Ceramic Pour-Over Coffee Set", "price": 64.00, "category": "Home", "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=400&fit=crop", "description": "Handcrafted ceramic dripper.", "stock": 40, "rating": 4.6},
        {"name": "Mechanical Keyboard TKL", "price": 229.00, "category": "Electronics", "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=400&fit=crop", "description": "Cherry MX Brown switches.", "stock": 25, "rating": 4.8},
        {"name": "Canvas Backpack 26L", "price": 89.00, "category": "Bags", "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop", "description": "Waxed canvas, leather trim.", "stock": 60, "rating": 4.5},
        {"name": "Stainless Steel Water Bottle", "price": 39.95, "category": "Home", "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&h=400&fit=crop", "description": "Triple-wall vacuum insulation.", "stock": 100, "rating": 4.7},
        {"name": "Merino Wool Crew Sweater", "price": 119.00, "category": "Clothing", "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=400&fit=crop", "description": "100% superfine merino.", "stock": 45, "rating": 4.6},
    ]
    for item in items:
        await products.insert_one(item)

    print("Firestore seeded with demo data")
