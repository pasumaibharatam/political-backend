from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
import os, uuid, urllib.parse

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch

# ===================== APP =====================
app = FastAPI()

# ===================== CORS =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://pasumaibharatam.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== CONFIG (ONLY ADMIN LOGIN) =====================
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN credentials not set")

ALGORITHM = "HS256"

UPLOAD_DIR = "uploads"
IDCARD_DIR = "idcards"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IDCARD_DIR, exist_ok=True)

# ===================== DB (UNCHANGED) =====================
USERNAME = "pasumaibharatam_db_user"
PASSWORD = urllib.parse.quote_plus("pasumai123")
CLUSTER = "pasumai.mrsonfr.mongodb.net"

MONGO_URL = f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URL)
db = client["political_db"]
districts_collection = db["districts"]
candidates_collection = db["candidates"]

# ===================== JWT HELPERS =====================
def create_jwt_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=6)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===================== AUTH =====================
class LoginSchema(BaseModel):
    username: str
    password: str

def verify_admin(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")
    payload = decode_jwt(token)

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return payload

# ===================== ADMIN LOGIN =====================
@app.post("/admin/login")
def admin_login(data: LoginSchema):
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        token = create_jwt_token({"role": "admin"})
        return {"token": token}

    raise HTTPException(status_code=401, detail="Invalid credentials")

# ===================== ADMIN DATA =====================
@app.get("/admin")
def get_all_candidates(admin=Depends(verify_admin)):
    candidates = list(
        candidates_collection.find(
            {},
            {"_id": 1, "name": 1, "mobile": 1, "district": 1, "gender": 1, "age": 1}
        )
    )

    for c in candidates:
        c["_id"] = str(c["_id"])

    return candidates

# ===================== STATIC =====================
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/idcards", StaticFiles(directory=IDCARD_DIR), name="idcards")
