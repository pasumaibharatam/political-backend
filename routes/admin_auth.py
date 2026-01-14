from fastapi import APIRouter, HTTPException, Response, Request, Depends
from db import admins_collection
from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

# -------- CREATE ADMIN --------
@router.post("/create-admin")
def create_admin(data: dict):
    try:
        admin = {
            "username": data["username"],
            "password": hash_password(data["password"]),
            "role": "admin",
            "is_active": True
        }
        admins_collection.insert_one(admin)
        return {"message": "Admin created"}
    except Exception as e:
        print("❌ Error creating admin:", e)
        raise HTTPException(status_code=500, detail=str(e))


# -------- LOGIN --------
@router.post("/login")
def admin_login(data: dict, response: Response):
    admin = admins_collection.find_one({"username": data["username"]})

    if not admin or not verify_password(data["password"], admin["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": admin["username"], "role": admin["role"]})

    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=True,      # Render requires HTTPS
        samesite="none"
    )

    return {"message": "Login successful"}

# -------- AUTH DEPENDENCY --------
def get_current_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
