from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    class_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[bool] = mapped_column(Boolean, default=True)

    students: Mapped[List["Student"]] = relationship("Student", back_populates="classroom")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=False)

    classroom: Mapped[Optional["Classroom"]] = relationship("Classroom", back_populates="students")