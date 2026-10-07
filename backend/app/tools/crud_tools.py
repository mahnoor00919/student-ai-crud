"""
Controlled CRUD tools. The LLM never touches the database directly.
These tools wrap StudentService and return plain dicts for the graph.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from pydantic import ValidationError
from fastapi import HTTPException

from app.models.student import StudentCreate, StudentUpdate
from app.services.student_service import StudentService


class CRUDTools:
    def __init__(self, db: Session):
        self.db = db

    def create_student(
        self,
        name: str,
        roll_number: int,
        age: int,
        email: str,
    ) -> Dict[str, Any]:
        try:
            data = StudentCreate(name=name, roll_number=roll_number, age=age, email=email)
            student = StudentService.create(self.db, data)
            return {
                "success": True,
                "operation": "CREATE",
                "message": f"Student '{student.name}' (roll {student.roll_number}) created successfully.",
                "student": student.model_dump(),
            }
        except ValidationError as e:
            return {"success": False, "operation": "CREATE", "error": str(e), "message": f"Validation error: {e}"}
        except HTTPException as e:
            return {"success": False, "operation": "CREATE", "error": e.detail, "message": e.detail}
        except Exception as e:
            return {"success": False, "operation": "CREATE", "error": str(e), "message": f"Unexpected error: {e}"}

    def get_students(self) -> Dict[str, Any]:
        try:
            students = StudentService.get_all(self.db)
            return {
                "success": True,
                "operation": "READ_ALL",
                "message": f"Found {len(students)} student(s).",
                "students": [s.model_dump() for s in students],
                "count": len(students),
            }
        except Exception as e:
            return {"success": False, "operation": "READ_ALL", "error": str(e), "message": f"Error listing students: {e}"}

    def get_student(
        self,
        student_id: Optional[int] = None,
        roll_number: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            if student_id is not None:
                student = StudentService.get_by_id(self.db, student_id)
                return {
                    "success": True,
                    "operation": "READ_ONE",
                    "message": f"Found student '{student.name}'.",
                    "student": student.model_dump(),
                }
            if roll_number is not None:
                student = StudentService.get_by_roll(self.db, roll_number)
                if not student:
                    return {
                        "success": False,
                        "operation": "READ_ONE",
                        "error": "not_found",
                        "message": f"No student found with roll number {roll_number}.",
                    }
                return {
                    "success": True,
                    "operation": "READ_ONE",
                    "message": f"Found student '{student.name}'.",
                    "student": student.model_dump(),
                }
            if name:
                matches = StudentService.find_by_name(self.db, name)
                if len(matches) == 0:
                    return {
                        "success": False,
                        "operation": "READ_ONE",
                        "error": "not_found",
                        "message": f"No student found matching name '{name}'.",
                    }
                if len(matches) > 1:
                    return {
                        "success": False,
                        "operation": "READ_ONE",
                        "error": "ambiguous",
                        "message": f"Multiple students match '{name}'. Please specify roll number.",
                        "matches": [s.model_dump() for s in matches],
                    }
                student = matches[0]
                return {
                    "success": True,
                    "operation": "READ_ONE",
                    "message": f"Found student '{student.name}'.",
                    "student": student.model_dump(),
                }
            return {
                "success": False,
                "operation": "READ_ONE",
                "error": "missing_identifier",
                "message": "Please provide a student id, roll number, or name.",
            }
        except HTTPException as e:
            return {"success": False, "operation": "READ_ONE", "error": e.detail, "message": e.detail}
        except Exception as e:
            return {"success": False, "operation": "READ_ONE", "error": str(e), "message": f"Error: {e}"}

    def update_student(
        self,
        student_id: Optional[int] = None,
        roll_number: Optional[int] = None,
        name: Optional[str] = None,
        new_name: Optional[str] = None,
        new_roll_number: Optional[int] = None,
        new_age: Optional[int] = None,
        new_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            # Resolve target student
            target_id: Optional[int] = None
            if student_id is not None:
                target_id = student_id
            elif roll_number is not None:
                s = StudentService.get_by_roll(self.db, roll_number)
                if not s:
                    return {
                        "success": False,
                        "operation": "UPDATE",
                        "error": "not_found",
                        "message": f"No student found with roll number {roll_number}.",
                    }
                target_id = s.id
            elif name:
                matches = StudentService.find_by_name(self.db, name)
                if len(matches) == 0:
                    return {
                        "success": False,
                        "operation": "UPDATE",
                        "error": "not_found",
                        "message": f"No student found matching name '{name}'.",
                    }
                if len(matches) > 1:
                    return {
                        "success": False,
                        "operation": "UPDATE",
                        "error": "ambiguous",
                        "message": f"Multiple students match '{name}'. Please specify roll number.",
                        "matches": [s.model_dump() for s in matches],
                    }
                target_id = matches[0].id
            else:
                return {
                    "success": False,
                    "operation": "UPDATE",
                    "error": "missing_identifier",
                    "message": "Please identify the student (id, roll number, or unique name).",
                }

            update_payload: Dict[str, Any] = {}
            if new_name is not None:
                update_payload["name"] = new_name
            if new_roll_number is not None:
                update_payload["roll_number"] = new_roll_number
            if new_age is not None:
                update_payload["age"] = new_age
            if new_email is not None:
                update_payload["email"] = new_email

            if not update_payload:
                return {
                    "success": False,
                    "operation": "UPDATE",
                    "error": "nothing_to_update",
                    "message": "No fields provided to update.",
                }

            data = StudentUpdate(**update_payload)
            student = StudentService.update(self.db, target_id, data)
            return {
                "success": True,
                "operation": "UPDATE",
                "message": f"Student '{student.name}' (roll {student.roll_number}) updated successfully.",
                "student": student.model_dump(),
            }
        except ValidationError as e:
            return {"success": False, "operation": "UPDATE", "error": str(e), "message": f"Validation error: {e}"}
        except HTTPException as e:
            return {"success": False, "operation": "UPDATE", "error": e.detail, "message": e.detail}
        except Exception as e:
            return {"success": False, "operation": "UPDATE", "error": str(e), "message": f"Unexpected error: {e}"}

    def delete_student(
        self,
        student_id: Optional[int] = None,
        roll_number: Optional[int] = None,
        name: Optional[str] = None,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        try:
            if student_id is not None:
                target = StudentService.get_by_id(self.db, student_id)
            elif roll_number is not None:
                target = StudentService.get_by_roll(self.db, roll_number)
                if not target:
                    return {
                        "success": False,
                        "operation": "DELETE",
                        "error": "not_found",
                        "message": f"No student found with roll number {roll_number}.",
                    }
            elif name:
                matches = StudentService.find_by_name(self.db, name)
                if len(matches) == 0:
                    return {
                        "success": False,
                        "operation": "DELETE",
                        "error": "not_found",
                        "message": f"No student found matching name '{name}'.",
                    }
                if len(matches) > 1:
                    return {
                        "success": False,
                        "operation": "DELETE",
                        "error": "ambiguous",
                        "message": f"Multiple students match '{name}'. Please specify the roll number to delete safely.",
                        "matches": [s.model_dump() for s in matches],
                    }
                target = matches[0]
            else:
                return {
                    "success": False,
                    "operation": "DELETE",
                    "error": "missing_identifier",
                    "message": "Please identify the student to delete (id or roll number preferred).",
                }

            if not confirm:
                return {
                    "success": False,
                    "operation": "DELETE",
                    "error": "confirmation_required",
                    "message": (
                        f"About to delete student '{target.name}' "
                        f"(id={target.id}, roll={target.roll_number}). "
                        "Reply with confirmation (e.g. 'yes, delete roll {target.roll_number}') to proceed."
                    ),
                    "pending_delete": target.model_dump(),
                }

            result = StudentService.delete(self.db, target.id)
            return {
                "success": True,
                "operation": "DELETE",
                "message": result["message"],
                "deleted_id": result["id"],
            }
        except HTTPException as e:
            return {"success": False, "operation": "DELETE", "error": e.detail, "message": e.detail}
        except Exception as e:
            return {"success": False, "operation": "DELETE", "error": str(e), "message": f"Unexpected error: {e}"}
