from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
import os
import urllib.parse
from routes import admin_auth, admin_routes

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

# ===================== DIRECTORIES =====================
UPLOAD_DIR = "uploads"
IDCARD_DIR = "idcards"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IDCARD_DIR, exist_ok=True)

# ===================== DATABASE =====================
# USERNAME = "pasumaibharatam_db_user"
# PASSWORD = urllib.parse.quote_plus("pasumai123")
# CLUSTER = "pasumai.mrsonfr.mongodb.net"

# MONGO_URL = (
#     f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/"
#     "?retryWrites=true&w=majority"
# )

# client = MongoClient(MONGO_URL)
# db = client["political_db"]
# candidates_collection = db["candidates"]
# admins_collection = db["admins"]
app.include_router(admin_auth.router)
app.include_router(admin_routes.router)
# ===================== ADMIN PAGE (NO AUTH) =====================
@app.get("/admin")
def get_all_candidates():
    candidates = list(
        candidates_collection.find(
            {},
            {
                "_id": 1,
                "name": 1,
                "mobile": 1,
                "district": 1,
                "gender": 1,
                "age": 1,
            }
        )
    )

    for c in candidates:
        c["_id"] = str(c["_id"])

    return candidates

# ===================== STATIC FILES =====================
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/idcards", StaticFiles(directory=IDCARD_DIR), name="idcards")


