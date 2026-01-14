from pymongo import MongoClient
import os
import urllib.parse
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
admins_collection = db["admins"]