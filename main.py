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

from reportlab.lib.pagesizes import A6
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

# ===================== CONFIG =====================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"   # move to env later

SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"

UPLOAD_DIR = "uploads"
IDCARD_DIR = "idcards"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IDCARD_DIR, exist_ok=True)

# ===================== DB =====================
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
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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

# ===================== DISTRICTS =====================
tamil_nadu_districts = [
    "Ariyalur","Chengalpattu","Chennai","Coimbatore","Cuddalore",
    "Dharmapuri","Dindigul","Erode","Kallakurichi","Kancheepuram",
    "Karur","Krishnagiri","Madurai","Mayiladuthurai","Nagapattinam",
    "Namakkal","Nilgiris","Perambalur","Pudukkottai","Ramanathapuram",
    "Ranipet","Salem","Sivagangai","Tenkasi","Thanjavur","Theni",
    "Thoothukudi","Tiruchirappalli","Tirunelveli","Tirupathur",
    "Tiruppur","Tiruvallur","Tiruvannamalai","Tiruvarur",
    "Vellore","Viluppuram","Virudhunagar"
]

@app.on_event("startup")
async def startup():
    districts_collection.create_index("name", unique=True)
    for d in tamil_nadu_districts:
        districts_collection.update_one(
            {"name": d},
            {"$setOnInsert": {"name": d}},
            upsert=True
        )

@app.get("/districts")
def get_districts():
    return list(districts_collection.find({}, {"_id": 0}))

# ===================== REGISTER =====================
def normalize(val):
    return val if val not in [None, ""] else ""

@app.post("/register")
async def register(
    name: str = Form(...),
    age: int = Form(...),
    gender: Optional[str] = Form(None),
    mobile: str = Form(...),
    state: str = Form(...),
    district: str = Form(...),
    photo: UploadFile = File(None)
):
    mobile = mobile.strip()
    if not mobile.isdigit() or len(mobile) != 10:
        raise HTTPException(400, "Invalid mobile number")

    if candidates_collection.find_one({"mobile": mobile}):
        raise HTTPException(400, "Mobile already registered")

    photo_path = ""
    if photo:
        ext = photo.filename.split(".")[-1]
        photo_path = f"{UPLOAD_DIR}/{uuid.uuid4()}.{ext}"
        with open(photo_path, "wb") as f:
            f.write(await photo.read())

    candidate = {
        "name": name,
        "age": age,
        "gender": normalize(gender),
        "mobile": mobile,
        "state": state,
        "district": district,
        "photo": photo_path,
        "created_at": datetime.utcnow()
    }

    candidates_collection.insert_one(candidate)
    generate_id_card(candidate)

    return {"message": "Registration successful"}

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

# ===================== ID CARD =====================
def generate_id_card(candidate):
    CARD_WIDTH = 3.5 * inch
    CARD_HEIGHT = 2 * inch

    pdf_path = f"{IDCARD_DIR}/{candidate['mobile']}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    DARK_GREEN = HexColor("#1B5E20")
    LIGHT_GREEN = HexColor("#E8F5E9")
    GREY = HexColor("#424242")

    c.setFillColor(LIGHT_GREEN)
    c.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=1)

    c.setFillColor(DARK_GREEN)
    c.rect(0, 0, 18, CARD_HEIGHT, fill=1)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_GREEN)
    c.drawString(30, CARD_HEIGHT - 22, "PASUMAI BHARATAM")

    c.setFont("Helvetica", 7)
    c.setFillColor(GREY)
    c.drawString(30, CARD_HEIGHT - 35, "Membership Identity Card")

    if candidate.get("photo") and os.path.exists(candidate["photo"]):
        c.drawImage(candidate["photo"], CARD_WIDTH - 60, CARD_HEIGHT - 70, 45, 55)

    c.setFont("Helvetica", 7)
    c.drawString(30, CARD_HEIGHT - 60, f"Name: {candidate['name']}")
    c.drawString(30, CARD_HEIGHT - 75, f"Mobile: {candidate['mobile']}")
    c.drawString(30, CARD_HEIGHT - 90, f"District: {candidate['district']}")

    c.save()

@app.get("/download-id/{mobile}")
def download_id(mobile: str):
    pdf_path = f"{IDCARD_DIR}/{mobile}.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "ID card not found")

    return FileResponse(pdf_path, filename=f"{mobile}_ID.pdf")

# ===================== STATIC =====================
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/idcards", StaticFiles(directory=IDCARD_DIR), name="idcards")
