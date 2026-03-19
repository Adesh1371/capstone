from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from database import get_collection
from utils.security import get_password_hash, verify_password, create_access_token
# from .mailer import send_welcome_email
from utils.mailer import send_welcome_email
from middleware.auth import get_current_user
# from auth_middleware import get_current_user
import asyncio

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: dict | None = None

@router.post("/register")
async def register(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    users = get_collection("users")
    existing = await users.find_one({"email": req.email})
    if existing:
        raise HTTPException(400, "Email already registered")
    user_id = await users.insert_one({
        "name": req.name,
        "email": req.email,
        "hashed_password": get_password_hash(req.password),
        "role": "user",
        "address": {}
    })
    token = create_access_token({"sub": user_id, "email": req.email, "role": "user"})
    asyncio.create_task(send_welcome_email(req.email, req.name))
    return {"token": token, "user": {"_id": user_id, "name": req.name, "email": req.email, "role": "user"}}

@router.post("/login")
async def login(req: LoginRequest):
    users = get_collection("users")
    user = await users.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token({"sub": user["_id"], "email": user["email"], "role": user.get("role", "user")})
    return {"token": token, "user": {"_id": user["_id"], "name": user["name"], "email": user["email"], "role": user.get("role", "user")}}

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != "hashed_password"}

@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, user=Depends(get_current_user)):
    users = get_collection("users")
    update = {}
    if req.name: update["name"] = req.name
    if req.phone: update["phone"] = req.phone
    if req.address: update["address"] = req.address
    await users.update_one({"_id": user["_id"]}, {"$set": update})
    return {"message": "Profile updated"}