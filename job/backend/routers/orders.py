from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_collection
from middleware.auth import get_current_user, require_admin
from utils.mailer import send_order_confirmation
import asyncio, random, string

router = APIRouter(prefix="/api/orders", tags=["orders"])

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]

class PaymentDetails(BaseModel):
    card_number: str
    expiry: str
    cvv: str
    name_on_card: str

class PlaceOrderRequest(BaseModel):
    shipping_address: dict
    payment: PaymentDetails
    notes: Optional[str] = None

class UpdateStatusRequest(BaseModel):
    status: str

def _simulate_payment(payment: PaymentDetails) -> dict:
    """Simulates payment processing. Always succeeds for demo."""
    return {
        "success": True,
        "transaction_id": "TXN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12)),
        "gateway": "ShopFlow Payments",
        "card_last4": payment.card_number.replace(" ","")[-4:],
        "amount_charged": None  # filled by caller
    }

@router.post("")
async def place_order(req: PlaceOrderRequest, user=Depends(get_current_user)):
    carts = get_collection("cart")
    cart = await carts.find_one({"user_id": user["_id"]})
    if not cart or not cart.get("items"):
        raise HTTPException(400, "Cart is empty")

    products = get_collection("products")
    items = []
    total = 0
    for ci in cart["items"]:
        p = await products.find_one({"_id": ci["product_id"]})
        if not p:
            raise HTTPException(404, f"Product {ci['product_id']} not found")
        if p.get("stock", 0) < ci["quantity"]:
            raise HTTPException(400, f"Insufficient stock for {p['name']}")
        subtotal = p["price"] * ci["quantity"]
        items.append({"product_id": ci["product_id"], "name": p["name"], "price": p["price"], "quantity": ci["quantity"], "subtotal": subtotal, "image": p.get("image","")})
        total += subtotal

    payment_result = _simulate_payment(req.payment)
    payment_result["amount_charged"] = round(total, 2)

    orders = get_collection("orders")
    order_id = await orders.insert_one({
        "user_id": user["_id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "items": items,
        "total": round(total, 2),
        "shipping_address": req.shipping_address,
        "payment": {
            "transaction_id": payment_result["transaction_id"],
            "gateway": payment_result["gateway"],
            "card_last4": payment_result["card_last4"],
            "status": "paid"
        },
        "status": "confirmed",
        "notes": req.notes or "",
        "timeline": [{"status": "confirmed", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}]
    })

    # Deduct stock
    for ci in cart["items"]:
        p = await products.find_one({"_id": ci["product_id"]})
        if p:
            await products.update_one({"_id": ci["product_id"]}, {"$set": {"stock": max(0, p["stock"] - ci["quantity"])}})

    # Clear cart
    await carts.update_one({"user_id": user["_id"]}, {"$set": {"items": []}})

    order = await orders.find_one({"_id": order_id})
    asyncio.create_task(send_order_confirmation(user["email"], user["name"], order))

    return {"message": "Order placed successfully", "order_id": order_id, "transaction_id": payment_result["transaction_id"], "total": round(total, 2)}

@router.get("")
async def my_orders(user=Depends(get_current_user)):
    orders = get_collection("orders")
    docs = await orders.find({"user_id": user["_id"]}, sort=[("created_at", -1)])
    return {"orders": docs}

@router.get("/all")
async def all_orders(admin=Depends(require_admin)):
    orders = get_collection("orders")
    docs = await orders.find(sort=[("created_at", -1)])
    return {"orders": docs}

@router.get("/{order_id}")
async def get_order(order_id: str, user=Depends(get_current_user)):
    orders = get_collection("orders")
    order = await orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(404, "Order not found")
    if order["user_id"] != user["_id"] and user.get("role") != "admin":
        raise HTTPException(403, "Access denied")
    return order

@router.put("/{order_id}/status")
async def update_status(order_id: str, req: UpdateStatusRequest, admin=Depends(require_admin)):
    if req.status not in ORDER_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {ORDER_STATUSES}")
    orders = get_collection("orders")
    order = await orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(404, "Order not found")
    timeline = order.get("timeline", [])
    timeline.append({"status": req.status, "timestamp": __import__("datetime").datetime.utcnow().isoformat()})
    await orders.update_one({"_id": order_id}, {"$set": {"status": req.status, "timeline": timeline}})
    return {"message": "Status updated"}

@router.put("/{order_id}/cancel")
async def cancel_order(order_id: str, user=Depends(get_current_user)):
    orders = get_collection("orders")
    order = await orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(404, "Order not found")
    if order["user_id"] != user["_id"]:
        raise HTTPException(403, "Access denied")
    if order["status"] not in ["pending", "confirmed"]:
        raise HTTPException(400, "Cannot cancel order in current status")
    timeline = order.get("timeline", [])
    timeline.append({"status": "cancelled", "timestamp": __import__("datetime").datetime.utcnow().isoformat()})
    await orders.update_one({"_id": order_id}, {"$set": {"status": "cancelled", "timeline": timeline}})
    return {"message": "Order cancelled"}
