from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("roll_number", name="uq_roll_number"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    roll_number = Column(Integer, nullable=False, unique=True, index=True)
    age = Column(Integer, nullable=False)
    email = Column(String(150), nullable=False)


# ---------- Pydantic schemas ----------

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    roll_number: int = Field(..., ge=1)
    age: int = Field(..., ge=1, le=120)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    roll_number: Optional[int] = Field(None, ge=1)
    age: Optional[int] = Field(None, ge=1, le=120)
    email: Optional[EmailStr] = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty")
        return v


class StudentOut(BaseModel):
    id: int
    name: str
    roll_number: int
    age: int
    email: str

    model_config = {"from_attributes": True}
