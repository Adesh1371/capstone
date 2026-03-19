from fastapi import APIRouter, Query, Depends
from database import get_collection
from middleware.auth import require_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/products", tags=["products"])

class ProductCreate(BaseModel):
    name: str
    price: float
    category: str
    image: str
    description: str
    stock: int = 0
    rating: float = 0.0

@router.get("")
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    products = get_collection("products")
    query = {}
    if category:
        query["category"] = category
    docs = await products.find(query, sort=[("created_at", -1)], skip=skip, limit=limit)
    if search:
        s = search.lower()
        docs = [d for d in docs if s in d["name"].lower() or s in d.get("description","").lower()]
    return {"products": docs, "total": len(docs)}

@router.get("/categories")
async def get_categories():
    products = get_collection("products")
    docs = await products.find()
    cats = list(set(d.get("category","") for d in docs))
    return {"categories": sorted(cats)}

@router.get("/{product_id}")
async def get_product(product_id: str):
    products = get_collection("products")
    p = await products.find_one({"_id": product_id})
    if not p:
        from fastapi import HTTPException
        raise HTTPException(404, "Product not found")
    return p

@router.post("")
async def create_product(req: ProductCreate, admin=Depends(require_admin)):
    products = get_collection("products")
    pid = await products.insert_one(req.model_dump())
    return {"_id": pid, **req.model_dump()}

@router.put("/{product_id}")
async def update_product(product_id: str, req: ProductCreate, admin=Depends(require_admin)):
    products = get_collection("products")
    await products.update_one({"_id": product_id}, {"$set": req.model_dump()})
    return {"message": "Updated"}
