from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, Any

from database import engine, get_db, Base
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Management API")

def format_response(status_code: int, message: str, path: str, data: Any = None, error: Any = None):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "path": path
    }

class BusinessException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_response(
            status_code=exc.status_code,
            message=exc.message,
            path=request.url.path,
            error=exc.message
        )
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_response(
            status_code=422,
            message="Dữ liệu đầu vào không hợp lệ",
            path=request.url.path,
            error=exc.errors()
        )
    )

def check_student_constraints(db: Session, student_data: schemas.StudentBase, current_student_id: Optional[int] = None):
    classroom = db.query(models.Classroom).filter(models.Classroom.id == student_data.class_id).first()
    if not classroom:
        raise BusinessException(400, "Lớp học không tồn tại")
    
    if not classroom.status:
        raise BusinessException(400, "Lớp học hiện tại không hoạt động")

    code_query = db.query(models.Student).filter(models.Student.student_code == student_data.student_code)
    if current_student_id:
        code_query = code_query.filter(models.Student.id != current_student_id)
    if code_query.first():
        raise BusinessException(400, "Mã sinh viên đã tồn tại")

    email_query = db.query(models.Student).filter(models.Student.email == student_data.email)
    if current_student_id:
        email_query = email_query.filter(models.Student.id != current_student_id)
    if email_query.first():
        raise BusinessException(400, "Email đã tồn tại")

    current_student_count = db.query(models.Student).filter(models.Student.class_id == student_data.class_id).count()
    
    if current_student_id:
        existing_student = db.query(models.Student).filter(models.Student.id == current_student_id).first()
        if existing_student and existing_student.class_id == student_data.class_id:
            current_student_count -= 1

    if current_student_count >= classroom.max_students:
        raise BusinessException(400, "Lớp học đã đủ số lượng sinh viên")

@app.get("/students", response_model=schemas.APIResponse)
def get_students(
    request: Request,
    search: Optional[str] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Student)

    if class_id:
        query = query.filter(models.Student.class_id == class_id)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Student.full_name.ilike(search_filter)) |
            (models.Student.student_code.ilike(search_filter)) |
            (models.Student.email.ilike(search_filter))
        )

    students = query.all()
    data = [schemas.StudentResponse.model_validate(s).model_dump() for s in students]

    return format_response(
        status_code=200,
        message="Lấy danh sách sinh viên thành công",
        path=request.url.path,
        data=data
    )

@app.get("/students/{student_id}", response_model=schemas.APIResponse)
def get_student_detail(student_id: int, request: Request, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise BusinessException(404, "Không tìm thấy sinh viên")

    data = schemas.StudentResponse.model_validate(student).model_dump()
    return format_response(
        status_code=200,
        message="Lấy thông tin sinh viên thành công",
        path=request.url.path,
        data=data
    )

@app.post("/students", response_model=schemas.APIResponse, status_code=201)
def create_student(student_in: schemas.StudentCreate, request: Request, db: Session = Depends(get_db)):
    check_student_constraints(db, student_in)

    new_student = models.Student(**student_in.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    data = schemas.StudentResponse.model_validate(new_student).model_dump()
    
    return JSONResponse(
        status_code=201,
        content=format_response(
            status_code=201,
            message="Thêm mới sinh viên thành công",
            path=request.url.path,
            data=data
        )
    )

@app.put("/students/{student_id}", response_model=schemas.APIResponse)
def update_student(student_id: int, student_in: schemas.StudentUpdate, request: Request, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise BusinessException(404, "Không tìm thấy sinh viên")

    check_student_constraints(db, student_in, current_student_id=student_id)

    for field, value in student_in.model_dump().items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)

    data = schemas.StudentResponse.model_validate(student).model_dump()
    return format_response(
        status_code=200,
        message="Cập nhật thông tin sinh viên thành công",
        path=request.url.path,
        data=data
    )