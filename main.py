from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from routes import admin_auth, admin_routes
from pymongo import MongoClient

import urllib.parse
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://pasumaibharatam.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
USERNAME = "pasumaibharatam_db_user"
PASSWORD = urllib.parse.quote_plus("pasumai123")
CLUSTER = "pasumai.mrsonfr.mongodb.net"

MONGO_URL = (
    f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/"
    "?retryWrites=true&w=majority"
)

client = MongoClient(MONGO_URL)
db = client["political_db"]
candidates_collection = db["candidates"]
# Directories
UPLOAD_DIR = "uploads"
IDCARD_DIR = "idcards"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IDCARD_DIR, exist_ok=True)

# Routers
app.include_router(admin_auth.router)
app.include_router(admin_routes.router)

# Static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/idcards", StaticFiles(directory=IDCARD_DIR), name="idcards")
