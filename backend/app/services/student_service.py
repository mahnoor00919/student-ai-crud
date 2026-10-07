from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.student import Student, StudentCreate, StudentUpdate, StudentOut


class StudentService:
    """Controlled CRUD service – the only layer that talks to the DB."""

    @staticmethod
    def create(db: Session, data: StudentCreate) -> StudentOut:
        existing = db.query(Student).filter(Student.roll_number == data.roll_number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student with roll number {data.roll_number} already exists.",
            )
        student = Student(
            name=data.name,
            roll_number=data.roll_number,
            age=data.age,
            email=str(data.email),
        )
        db.add(student)
        try:
            db.commit()
            db.refresh(student)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not create student due to a constraint violation.",
            )
        return StudentOut.model_validate(student)

    @staticmethod
    def get_all(db: Session) -> List[StudentOut]:
        students = db.query(Student).order_by(Student.id).all()
        return [StudentOut.model_validate(s) for s in students]

    @staticmethod
    def get_by_id(db: Session, student_id: int) -> StudentOut:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with id {student_id} not found.")
        return StudentOut.model_validate(student)

    @staticmethod
    def get_by_roll(db: Session, roll_number: int) -> Optional[StudentOut]:
        student = db.query(Student).filter(Student.roll_number == roll_number).first()
        if not student:
            return None
        return StudentOut.model_validate(student)

    @staticmethod
    def find_by_name(db: Session, name: str) -> List[StudentOut]:
        """Case-insensitive partial match – used for ambiguity checks."""
        students = (
            db.query(Student)
            .filter(Student.name.ilike(f"%{name.strip()}%"))
            .order_by(Student.id)
            .all()
        )
        return [StudentOut.model_validate(s) for s in students]

    @staticmethod
    def update(db: Session, student_id: int, data: StudentUpdate) -> StudentOut:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with id {student_id} not found.")

        update_data = data.model_dump(exclude_unset=True)
        if "roll_number" in update_data:
            conflict = (
                db.query(Student)
                .filter(Student.roll_number == update_data["roll_number"], Student.id != student_id)
                .first()
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Roll number {update_data['roll_number']} is already taken.",
                )

        for key, value in update_data.items():
            if key == "email" and value is not None:
                value = str(value)
            setattr(student, key, value)

        try:
            db.commit()
            db.refresh(student)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not update student due to a constraint violation.",
            )
        return StudentOut.model_validate(student)

    @staticmethod
    def update_by_roll(db: Session, roll_number: int, data: StudentUpdate) -> StudentOut:
        student = db.query(Student).filter(Student.roll_number == roll_number).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with roll number {roll_number} not found.",
            )
        return StudentService.update(db, student.id, data)

    @staticmethod
    def delete(db: Session, student_id: int) -> dict:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with id {student_id} not found.")
        name = student.name
        roll = student.roll_number
        db.delete(student)
        db.commit()
        return {"message": f"Student '{name}' (roll {roll}) deleted successfully.", "id": student_id}

    @staticmethod
    def delete_by_roll(db: Session, roll_number: int) -> dict:
        student = db.query(Student).filter(Student.roll_number == roll_number).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with roll number {roll_number} not found.",
            )
        return StudentService.delete(db, student.id)
