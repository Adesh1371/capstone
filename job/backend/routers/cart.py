from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_collection
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/cart", tags=["cart"])

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

@router.get("")
async def get_cart(user=Depends(get_current_user)):
    carts = get_collection("cart")
    cart = await carts.find_one({"user_id": user["_id"]})
    if not cart:
        return {"items": [], "total": 0}
    return await _enrich_cart(cart)

@router.post("/add")
async def add_to_cart(item: CartItem, user=Depends(get_current_user)):
    products = get_collection("products")
    product = await products.find_one({"_id": item.product_id})
    if not product:
        raise HTTPException(404, "Product not found")
    if product.get("stock", 0) < item.quantity:
        raise HTTPException(400, "Insufficient stock")

    carts = get_collection("cart")
    cart = await carts.find_one({"user_id": user["_id"]})
    if not cart:
        await carts.insert_one({"user_id": user["_id"], "items": [{"product_id": item.product_id, "quantity": item.quantity}]})
    else:
        items = cart.get("items", [])
        found = False
        for i in items:
            if i["product_id"] == item.product_id:
                i["quantity"] += item.quantity
                found = True
                break
        if not found:
            items.append({"product_id": item.product_id, "quantity": item.quantity})
        await carts.update_one({"user_id": user["_id"]}, {"$set": {"items": items}})
    return {"message": "Added to cart"}

@router.put("/update")
async def update_cart_item(item: CartItem, user=Depends(get_current_user)):
    carts = get_collection("cart")
    cart = await carts.find_one({"user_id": user["_id"]})
    if not cart:
        raise HTTPException(404, "Cart not found")
    items = cart.get("items", [])
    if item.quantity <= 0:
        items = [i for i in items if i["product_id"] != item.product_id]
    else:
        for i in items:
            if i["product_id"] == item.product_id:
                i["quantity"] = item.quantity
    await carts.update_one({"user_id": user["_id"]}, {"$set": {"items": items}})
    return {"message": "Cart updated"}

@router.delete("/clear")
async def clear_cart(user=Depends(get_current_user)):
    carts = get_collection("cart")
    await carts.update_one({"user_id": user["_id"]}, {"$set": {"items": []}})
    return {"message": "Cart cleared"}

async def _enrich_cart(cart: dict):
    products = get_collection("products")
    enriched = []
    total = 0
    for item in cart.get("items", []):
        p = await products.find_one({"_id": item["product_id"]})
        if p:
            line = {**item, "name": p["name"], "price": p["price"], "image": p.get("image",""), "subtotal": p["price"] * item["quantity"]}
            enriched.append(line)
            total += line["subtotal"]
    return {"items": enriched, "total": round(total, 2)}
