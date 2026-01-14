from fastapi import APIRouter, Depends
from routes.admin_auth import get_current_admin
from routes.admin_auth import get_current_admin
from db import candidates_collection 

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard")
def dashboard(admin=Depends(get_current_admin)):
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

# @router.get("/candidates")
# def get_candidates(admin=Depends(get_current_admin)):
#     return list(main.candidates_collection.find({}, {"_id": 0}))
