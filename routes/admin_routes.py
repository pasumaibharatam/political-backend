from fastapi import APIRouter, Depends
from routes.admin_auth import get_current_admin
import main  # 👈 import main

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard")
def dashboard(admin=Depends(get_current_admin)):
    return {
        "message": "Welcome Admin",
        "username": admin["sub"],
        "role": admin["role"]
    }

@router.get("/candidates")
def get_candidates(admin=Depends(get_current_admin)):
    return list(main.candidates_collection.find({}, {"_id": 0}))
