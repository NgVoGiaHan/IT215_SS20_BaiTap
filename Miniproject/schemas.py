from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any, Literal

class StudentBase(BaseModel):
    student_code: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=16, le=60)
    gender: Literal["male", "female", "other"]
    class_id: int = Field(..., ge=1)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class ClassroomResponse(BaseModel):
    id: int
    class_code: str
    class_name: str
    max_students: int
    status: bool

    class Config:
        from_attributes = True

class StudentResponse(StudentBase):
    id: int
    classroom: Optional[ClassroomResponse] = None

    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    statusCode: int
    message: str
    data: Optional[Any] = None
    error: Optional[Any] = None
    timestamp: str
    path: str