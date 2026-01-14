from fastapi import APIRouter, HTTPException, Response, Request
from jose import jwt, JWTError
from auth import verify_password, create_access_token, hash_password
from auth import SECRET_KEY, ALGORITHM
from db import admins_collection

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

@router.post("/login")
def admin_login(data: dict, response: Response):
    admin = admins_collection.find_one({"username": data["username"]})

    if not admin or not verify_password(data["password"], admin["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": admin["username"],
        "role": admin["role"]
    })

    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return {"message": "Login successful"}

# ---------- CREATE ADMIN ----------
@router.post("/create-admin")
def create_admin(data: dict):
    admin = {
        "username": data["username"],
        "password": hash_password(data["password"]),
        "role": data.get("role", "admin"),
        "is_active": True
    }

    admins_collection.insert_one(admin)
    return {"message": "Admin created"}

# ---------- AUTH DEPENDENCY ----------
def get_current_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401)
