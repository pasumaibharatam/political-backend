from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from routes import admin_auth, admin_routes

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://pasumaibharatam.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
