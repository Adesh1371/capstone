import os, sys, time
from pathlib import Path

_backend = Path(__file__).resolve().parent
_root    = _backend.parent

for _p in [str(_backend), str(_backend/"utils"), str(_backend/"middleware"), str(_backend/"routers")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv(str(_root / ".env"))

import importlib.util

def _load_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, str(filepath))
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_r       = _backend / "routers"
auth     = _load_module("routers.auth",     _r / "auth.py")
products = _load_module("routers.products", _r / "products.py")
cart     = _load_module("routers.cart",     _r / "cart.py")
orders   = _load_module("routers.orders",   _r / "orders.py")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import seed_demo_data

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(title="ShopFlow API", version="1.0.0",
              docs_url="/api/docs", redoc_url="/api/redoc")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "https://capstone-project-490610.web.app",
    "https://adesh.online",
    "https://www.adesh.online",
    "https://main.dxxegfccgtswk.amplifyapp.com",
    "http://localhost:3000",
    "http://localhost:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def handle_options(request: Request, call_next):
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    return await call_next(request)
@app.middleware("http")
async def security_headers(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Process-Time"] = f"{time.time()-start:.4f}"
    return response

# ── API routes first (must be before catch-all) ──────────────────
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

# ── Favicon (prevents 404 noise in browser console) ─────────────
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return HTMLResponse(status_code=204)

# ── Frontend catch-all (must be LAST) ───────────────────────────
frontend_index = _root / "frontend" / "index.html"

@app.get("/", include_in_schema=False)
async def root():
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
    return JSONResponse({"message": "ShopFlow API running", "docs": "/api/docs"})

@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    # Don't intercept API routes
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
    return JSONResponse({"message": "ShopFlow API running"})

# ── Startup ──────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    seed_demo_data()
    print("\n✅  ShopFlow running")
    print("    Frontend -> http://localhost:8000")
    print("    API Docs -> http://localhost:8000/api/docs")
    print("    Demo:  user@demo.com / demo1234")
    print("    Admin: admin@demo.com / admin1234\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
