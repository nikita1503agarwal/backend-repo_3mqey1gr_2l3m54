"""
Database Schemas for the Learning Platform (SaaS)

Each Pydantic model maps to a MongoDB collection whose name is the lowercase of the class name.
Example: class Course -> collection "course"
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(True, description="Active status")


class Lesson(BaseModel):
    title: str = Field(..., description="Lesson title")
    content: Optional[str] = Field(None, description="Lesson content (markdown)")
    video_url: Optional[str] = Field(None, description="Optional video URL")
    order: int = Field(..., ge=0, description="Lesson order in course")


class Course(BaseModel):
    title: str = Field(..., description="Course title")
    subtitle: Optional[str] = Field(None, description="Short subtitle")
    description: Optional[str] = Field(None, description="Detailed description")
    thumbnail_url: Optional[str] = Field(None, description="Course cover image")
    category: Optional[str] = Field(None, description="Category or topic")
    level: Optional[str] = Field(None, description="Beginner / Intermediate / Advanced")
    lessons: List[Lesson] = Field(default_factory=list, description="List of lessons")
    is_published: bool = Field(default=True, description="Visible to users")


class Enrollment(BaseModel):
    user_email: EmailStr = Field(..., description="Enrolled user's email")
    course_id: str = Field(..., description="ID of the course (stringified ObjectId)")
    status: str = Field(default="active", description="active | canceled")


class Progress(BaseModel):
    user_email: EmailStr = Field(..., description="User email")
    course_id: str = Field(..., description="Course ID (stringified ObjectId)")
    lesson_order: int = Field(..., ge=0, description="Which lesson order was completed")
    completed: bool = Field(default=False, description="Completion flag")
