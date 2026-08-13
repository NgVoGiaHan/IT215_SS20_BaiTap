from typing import Any
from fastapi import Depends, FastAPI, Request, Response, status
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
from schemas import EmployeesCreate, EmployeesSchemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def res(statusCode: int, message: str, data: Any = None, error: str | None = None, path: str = ""):
    return {
        "statusCode": statusCode,
        "message": message,
        "data": data,
        "error": error,
        "path": path,
    }


@app.get("/employees")
def get_employees(request: Request, db: Session = Depends(get_db)):
    employees = db.query(models.Employees).all()
    
    if not employees:
        return res(200, "Danh sách nhân viên rỗng!", [], None, request.url.path)

    data = [EmployeesSchemas.model_validate(emp).model_dump() for emp in employees]
    return res(200, "Lấy danh sách nhân viên thành công!", data, None, request.url.path)


@app.post("/employees")
def create_employee(
    request: Request,
    response: Response,
    payload: EmployeesCreate,
    db: Session = Depends(get_db)
):
    dept = db.query(models.Department).filter(models.Department.id == payload.department_id).first()
    if not dept:
        response.status_code = status.HTTP_404_NOT_FOUND
        return res(404, "Không tìm thấy phòng ban ban yêu cầu!", None, "ERR-DEPT-01", request.url.path)

    check_code = db.query(models.Employees).filter(models.Employees.employee_code == payload.employee_code).first()
    if check_code:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return res(400, "Mã nhân viên đã tồn tại trên hệ thống!", None, "ERR-EMPLOYEE-01", request.url.path)

    try:
        new_employee = models.Employees(**payload.model_dump())
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)

        response.status_code = status.HTTP_201_CREATED
        result_data = EmployeesSchemas.model_validate(new_employee).model_dump()
        return res(201, "Thêm mới nhân viên thành công!", result_data, None, request.url.path)

    except Exception as e:
        db.rollback()
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return res(500, "LỖI HỆ THỐNG!", None, str(e), request.url.path)