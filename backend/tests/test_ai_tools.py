"""
Tests for controlled CRUD tools (no real LLM).
Covers CREATE / READ / UPDATE / DELETE / missing / not-found / ambiguous paths.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = "sk-test-placeholder"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.student import Base
from app.tools.crud_tools import CRUDTools

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def tools():
    db = _TestSession()
    t = CRUDTools(db)
    yield t
    db.close()


def test_create_ok(tools):
    r = tools.create_student("Ali Khan", 23, 21, "ali@gmail.com")
    assert r["success"] is True
    assert r["student"]["roll_number"] == 23


def test_create_missing_validation(tools):
    r = tools.create_student("", 23, 21, "ali@gmail.com")
    assert r["success"] is False


def test_create_duplicate(tools):
    tools.create_student("Ali", 23, 21, "ali@gmail.com")
    r = tools.create_student("Bob", 23, 22, "bob@gmail.com")
    assert r["success"] is False
    assert "already exists" in r["message"].lower() or "roll" in r["message"].lower()


def test_get_all(tools):
    tools.create_student("A", 1, 20, "a@x.com")
    tools.create_student("B", 2, 21, "b@x.com")
    r = tools.get_students()
    assert r["success"] is True
    assert r["count"] == 2


def test_get_by_roll(tools):
    tools.create_student("Ali", 23, 21, "ali@gmail.com")
    r = tools.get_student(roll_number=23)
    assert r["success"] is True
    assert r["student"]["name"] == "Ali"


def test_get_not_found(tools):
    r = tools.get_student(roll_number=9999)
    assert r["success"] is False
    assert r["error"] == "not_found"


def test_update_by_roll(tools):
    tools.create_student("Ali", 23, 21, "ali@gmail.com")
    r = tools.update_student(roll_number=23, new_email="new@gmail.com")
    assert r["success"] is True
    assert r["student"]["email"] == "new@gmail.com"


def test_update_not_found(tools):
    r = tools.update_student(roll_number=9999, new_email="x@x.com")
    assert r["success"] is False
    assert r["error"] == "not_found"


def test_delete_requires_confirm(tools):
    tools.create_student("Ali", 23, 21, "ali@gmail.com")
    r = tools.delete_student(roll_number=23, confirm=False)
    assert r["success"] is False
    assert r["error"] == "confirmation_required"
    assert "pending_delete" in r


def test_delete_confirmed(tools):
    tools.create_student("Ali", 23, 21, "ali@gmail.com")
    r = tools.delete_student(roll_number=23, confirm=True)
    assert r["success"] is True
    r2 = tools.get_student(roll_number=23)
    assert r2["success"] is False


def test_ambiguous_name(tools):
    tools.create_student("Ali Khan", 23, 21, "ali@gmail.com")
    tools.create_student("Ali Ahmed", 24, 22, "ali2@gmail.com")
    r = tools.get_student(name="Ali")
    assert r["success"] is False
    assert r["error"] == "ambiguous"
    assert len(r["matches"]) == 2


def test_delete_ambiguous(tools):
    tools.create_student("Ali Khan", 23, 21, "ali@gmail.com")
    tools.create_student("Ali Ahmed", 24, 22, "ali2@gmail.com")
    r = tools.delete_student(name="Ali", confirm=False)
    assert r["success"] is False
    assert r["error"] == "ambiguous"
