from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pydantic import BaseModel
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
import urllib.parse
import os
import uuid

# -------------------- FastAPI --------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://pasumaibharatam.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
IDCARD_DIR = "idcards"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IDCARD_DIR, exist_ok=True)

# -------------------- MongoDB --------------------
# USERNAME = "pasumaibharatam_db_user"
# PASSWORD = urllib.parse.quote_plus("pasumai123")
# CLUSTER = "pasumai.mrsonfr.mongodb.net"

# MONGO_URL = f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/?retryWrites=true&w=majority&appName=Pasumai"
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000,
    connectTimeoutMS=3000,
     tls=True)
try:
    client.admin.command("ping")
    print("✅ MongoDB CONNECTED")
except Exception as e:
    print("❌ MongoDB FAILED:", e)
db = client["political_db"]
districts_collection = db["districts"]
candidates_collection = db["candidates"]

# -------------------- Districts --------------------
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
    global client, db, districts_collection, candidates_collection

    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000, tls=True)
        client.admin.command("ping")
        print("✅ MongoDB CONNECTED")

        db = client["political_db"]
        districts_collection = db["districts"]
        candidates_collection = db["candidates"]

        # create index async-safe (won’t block much)
        districts_collection.create_index("name", unique=True)

        # insert districts safely
        for d in tamil_nadu_districts:
            districts_collection.update_one(
                {"name": d},
                {"$setOnInsert": {"name": d}},
                upsert=True
            )

        print("✅ Districts verified")

    except Exception as e:
        print("❌ MongoDB CONNECTION FAILED:", e)



# -------------------- PDF GENERATOR --------------------
def generate_id_card(candidate):
    pdf_path = f"{IDCARD_DIR}/{candidate['mobile']}.pdf"

    c = canvas.Canvas(pdf_path, pagesize=A6)
    width, height = A6

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height-30, "MEMBERSHIP ID CARD")

    if candidate.get("photo"):
        c.drawImage(candidate["photo"], 20, height-140, 80, 100)

    c.setFont("Helvetica", 10)
    c.drawString(110, height-60, f"Name: {candidate['name']}")
    c.drawString(110, height-80, f"Mobile: {candidate['mobile']}")
    c.drawString(110, height-100, f"District: {candidate['district']}")
    c.drawString(110, height-120, f"State: {candidate['state']}")

    c.showPage()
    c.save()

    return pdf_path

# -------------------- ROUTES --------------------
@app.get("/")
def root():
    return {"status": "Backend running"}
@app.get("/test-db")
def test_db():
    count = candidates_collection.count_documents({})
    return {"message": "MongoDB connected", "records": count}
@app.get("/districts")
def get_districts():
    try:
        districts = list(districts_collection.find({}, {"_id": 0}).limit(50))
        return districts
    except Exception as e:
        return {"error": str(e)}
class Candidate(BaseModel):
    name: str
    mobile: str
    email: str | None = None
    voterId: str | None = None
    district: str
    state: str
@app.post("/register")
async def register(
    name: str = Form(...),
    mobile: str = Form(...),
    district: str = Form(...),
    state: str = Form(...),
    email: str = Form(None),
    voterId: str = Form(None),
    photo: UploadFile = File(None)
):
    photo_path = None

    if photo:
        ext = photo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        photo_path = f"{UPLOAD_DIR}/{filename}"
        with open(photo_path, "wb") as f:
            f.write(await photo.read())

    candidate = {
        "name": name,
        "mobile": mobile,
        "district": district,
        "state": state,
        "email": email,
        "voterId": voterId,
        "photo": photo_path
    }

    candidates_collection.insert_one(candidate)
    generate_id_card(candidate)

    return {"message": "Registration successful & ID generated"}
@app.get("/candidates")
def get_candidates():
    candidates = list(
        candidates_collection.find({}, {"_id": 0})
    )
    return candidates
@app.get("/download-id/{mobile}")
def download_id(mobile: str):
    candidate = candidates_collection.find_one({"mobile": mobile})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    pdf_path = f"{IDCARD_DIR}/{mobile}.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="ID card not generated")

    return FileResponse(pdf_path, filename=f"{mobile}_ID_Card.pdf")

# -------------------- STATIC --------------------
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/idcards", StaticFiles(directory="idcards"), name="idcards")

@app.delete("/candidates/{mobile}")
def delete_candidate(mobile: str):
    result = candidates_collection.delete_one({"mobile": mobile})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return {"message": "Candidate deleted successfully"}
