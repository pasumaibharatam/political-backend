from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
import os, uuid, urllib.parse
from datetime import datetime
from typing import Optional

# -------------------- APP --------------------
app = FastAPI()

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

# -------------------- DIRS --------------------
UPLOAD_DIR = "uploads"
IDCARD_DIR = "idcards"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IDCARD_DIR, exist_ok=True)

# -------------------- DB --------------------
USERNAME = "pasumaibharatam_db_user"
PASSWORD = urllib.parse.quote_plus("pasumai123")
CLUSTER = "pasumai.mrsonfr.mongodb.net"

MONGO_URL = f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URL)
db = client["political_db"]
districts_collection = db["districts"]
candidates_collection = db["candidates"]

# -------------------- HELPERS --------------------
def normalize(value):
    return value if value not in [None, ""] else ""

# -------------------- DISTRICTS --------------------
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

# -------------------- ROUTES --------------------
@app.get("/")
def root():
    return {"status": "Backend running"}

@app.get("/districts")
def get_districts():
    return list(districts_collection.find({}, {"_id": 0}))

# -------------------- REGISTER --------------------
@app.post("/register")
async def register(
    name: str = Form(...),
    father_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    age: int = Form(...),
    blood_group: str = Form(...),
    mobile: str = Form(...),
    email: Optional[str] = Form(None),
    state: str = Form(...),
    district: str = Form(...),
    local_body: str = Form(...),
    nagaram_type: str = Form(...),
    constituency: Optional[str] = Form(None),
    ward: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    voter_id: Optional[str] = Form(None),
    aadhaar: Optional[str] = Form(None),
    photo: UploadFile = File(None)
):
     # ✅ Normalize mobile
    mobile = str(mobile).strip()
    if len(mobile) != 10 or not mobile.isdigit():
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
        "father_name": normalize(father_name),
        "gender": normalize(gender),    
        "dob": normalize(dob),
        "age": age,
        "blood_group": blood_group,
        "mobile": mobile,
        "email": normalize(email),
        "state": state,
        "district": district,
        "local_body": normalize(local_body),
        "nagaram_type": normalize(nagaram_type),
        "constituency": normalize(constituency),
        "ward": normalize(ward),
        "address": normalize(address),
        "voter_id": normalize(voter_id),
        "aadhaar": normalize(aadhaar),
        "photo": photo_path,
        "created_at": datetime.utcnow()
    }

    candidates_collection.insert_one(candidate)
     # ✅ Generate ID card
    generate_id_card(candidate)

    return {
        "message": "Registration successful",
        "download_url": f"/download-id/{mobile}"
    }
# -------------------- PDF GENERATOR --------------------
def generate_id_card(candidate):
    CARD_WIDTH = 3.5 * inch
    CARD_HEIGHT = 2 * inch

    pdf_path = f"{IDCARD_DIR}/{candidate['mobile']}.pdf"
    os.makedirs(IDCARD_DIR, exist_ok=True)

    c = canvas.Canvas(pdf_path, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    # 🎨 Colors
    DARK_GREEN = HexColor("#1B5E20")
    LIGHT_GREEN = HexColor("#E8F5E9")
    WHITE = HexColor("#FFFFFF")
    GREY = HexColor("#424242")

    # 🔲 Background
    c.setFillColor(LIGHT_GREEN)
    c.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=1)

    # 🟩 Left color strip (modern style)
    c.setFillColor(DARK_GREEN)
    c.rect(0, 0, 18, CARD_HEIGHT, fill=1)

    # 🏷 Organization Name
    c.setFillColor(DARK_GREEN)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30, CARD_HEIGHT - 22, "PASUMAI BHARATAM")

    c.setFont("Helvetica", 7)
    c.setFillColor(GREY)
    c.drawString(30, CARD_HEIGHT - 34, "Membership Identity Card")

    # 📷 Photo (right side)
    if candidate.get("photo") and os.path.exists(candidate["photo"]):
        try:
            c.drawImage(
                candidate["photo"],
                CARD_WIDTH - 60,
                CARD_HEIGHT - 70,
                45,
                55,
                mask='auto'
            )
        except:
            pass

    # 📄 Member Details
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(DARK_GREEN)
    c.drawString(30, CARD_HEIGHT - 60, "Name")
    c.drawString(30, CARD_HEIGHT - 75, "Mobile")
    c.drawString(30, CARD_HEIGHT - 90, "District")

    c.setFont("Helvetica", 7)
    c.setFillColor(GREY)
    c.drawString(70, CARD_HEIGHT - 60, candidate.get("name", ""))
    c.drawString(70, CARD_HEIGHT - 75, candidate.get("mobile", ""))
    c.drawString(70, CARD_HEIGHT - 90, candidate.get("district", ""))

    # 🆔 ID Number (Bottom)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(DARK_GREEN)
    c.drawString(30, 18, f"ID: PB-{candidate.get('mobile', '')}")

    # 🌱 Tagline
    c.setFont("Helvetica-Oblique", 6)
    c.setFillColor(GREY)
    c.drawRightString(CARD_WIDTH - 12, 18, "Service • Integrity • Growth")

    c.showPage()
    c.save()

    return pdf_path

@app.get("/download-id/{mobile}")
def download_id(mobile: str):
    mobile = str(mobile).strip()

    # Try both string and int (for OLD DATA)
    candidate = candidates_collection.find_one(
        {"mobile": mobile}
    ) or candidates_collection.find_one(
        {"mobile": int(mobile)} if mobile.isdigit() else {}
    )

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    pdf_path = f"{IDCARD_DIR}/{mobile}.pdf"

    # 🔁 Auto-generate if missing
    if not os.path.exists(pdf_path):
        generate_id_card(candidate)

    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=500,
            detail="ID card generation failed"
        )

    return FileResponse(
        pdf_path,
        filename=f"{mobile}_ID_Card.pdf"
    )

# -------------------- STATIC --------------------
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/idcards", StaticFiles(directory=IDCARD_DIR), name="idcards")

@app.get("/admin")
def get_all_candidates():
    candidates = list(candidates_collection.find({}, {"_id": 1, "name": 1, "mobile": 1, "district": 1, "state": 1}))
    for c in candidates:
        c["_id"] = str(c["_id"])
    return candidates
