import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Course, Enrollment, Progress, User

app = FastAPI(title="Learning Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class CourseCreate(Course):
    pass


@app.get("/")
def root():
    return {"message": "Learning Platform API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Courses
@app.get("/api/courses")
def list_courses(limit: int = 50):
    docs = get_documents("course", {}, limit)
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify ObjectId
    return {"data": docs}


@app.post("/api/courses")
def create_course(payload: CourseCreate):
    inserted_id = create_document("course", payload)
    return {"id": inserted_id}


@app.get("/api/courses/{course_id}")
def get_course(course_id: str):
    doc = db["course"].find_one({"_id": ObjectId(course_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    doc["_id"] = str(doc["_id"])
    return doc


# Enrollment (simple listing/creation by email and course)
class EnrollmentCreate(Enrollment):
    pass


@app.post("/api/enrollments")
def enroll(enroll: EnrollmentCreate):
    # optional: ensure course exists
    course = db["course"].find_one({"_id": ObjectId(enroll.course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    inserted_id = create_document("enrollment", enroll)
    return {"id": inserted_id}


@app.get("/api/enrollments")
def list_enrollments(user_email: Optional[str] = None, course_id: Optional[str] = None, limit: int = 100):
    filt = {}
    if user_email:
        filt["user_email"] = user_email
    if course_id:
        filt["course_id"] = course_id
    docs = get_documents("enrollment", filt, limit)
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify
    return {"data": docs}


# Progress endpoints
class ProgressUpsert(Progress):
    pass


@app.post("/api/progress")
def upsert_progress(p: ProgressUpsert):
    # We will upsert by user_email + course_id + lesson_order
    filt = {
        "user_email": p.user_email,
        "course_id": p.course_id,
        "lesson_order": p.lesson_order,
    }
    existing = db["progress"].find_one(filt)
    payload = p.model_dump()
    if existing:
        payload["updated_at"] = existing.get("updated_at")  # will be set by create_document-like flow below
        db["progress"].update_one(filt, {"$set": payload}, upsert=True)
        doc = db["progress"].find_one(filt)
        doc["_id"] = str(doc["_id"])
        return doc
    else:
        inserted_id = create_document("progress", payload)
        doc = db["progress"].find_one({"_id": ObjectId(inserted_id)})
        doc["_id"] = str(doc["_id"])
        return doc


@app.get("/api/progress")
def list_progress(user_email: Optional[str] = None, course_id: Optional[str] = None, limit: int = 200):
    filt = {}
    if user_email:
        filt["user_email"] = user_email
    if course_id:
        filt["course_id"] = course_id
    docs = get_documents("progress", filt, limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"data": docs}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
