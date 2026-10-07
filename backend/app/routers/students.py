from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import StudentCreate, StudentUpdate, StudentOut
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    return StudentService.create(db, data)


@router.get("", response_model=List[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return StudentService.get_all(db)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return StudentService.get_by_id(db, student_id)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    return StudentService.update(db, student_id, data)


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    return StudentService.delete(db, student_id)
