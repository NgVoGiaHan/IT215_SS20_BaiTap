from pydantic import BaseModel, EmailStr, Field

class DepartmentSchema(BaseModel):
    id: int
    department_code: str
    department_name: str

    model_config = {"from_attributes": True}


class EmployeesCreate(BaseModel):
    employee_code: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department_id: int = Field(..., ge=1)


class EmployeesSchemas(BaseModel):
    id: int
    employee_code: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: DepartmentSchema

    model_config = {"from_attributes": True}