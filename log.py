from auth import hash_password
from db import admins_collection

admins_collection.insert_one({
    "username": "admin123",
    "password": hash_password("123"),
    "role": "admin",
    "is_active": True
})