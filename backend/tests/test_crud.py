"""
Unit tests for controlled CRUD service via FastAPI (no LLM required).
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Must set before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = "sk-test-placeholder"

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, init_db
from app.models.student import Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_student():
    r = client.post(
        "/students",
        json={"name": "Ali Khan", "roll_number": 23, "age": 21, "email": "ali@gmail.com"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["name"] == "Ali Khan"
    assert data["roll_number"] == 23
    assert data["age"] == 21
    assert data["email"] == "ali@gmail.com"
    assert "id" in data


def test_create_duplicate_roll():
    client.post(
        "/students",
        json={"name": "Ali Khan", "roll_number": 23, "age": 21, "email": "ali@gmail.com"},
    )
    r = client.post(
        "/students",
        json={"name": "Other", "roll_number": 23, "age": 22, "email": "other@gmail.com"},
    )
    assert r.status_code == 409


def test_list_students():
    client.post("/students", json={"name": "A", "roll_number": 1, "age": 20, "email": "a@x.com"})
    client.post("/students", json={"name": "B", "roll_number": 2, "age": 21, "email": "b@x.com"})
    r = client.get("/students")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_student():
    created = client.post(
        "/students",
        json={"name": "Ali", "roll_number": 23, "age": 21, "email": "ali@gmail.com"},
    ).json()
    r = client.get(f"/students/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Ali"


def test_get_not_found():
    r = client.get("/students/9999")
    assert r.status_code == 404


def test_update_student():
    created = client.post(
        "/students",
        json={"name": "Ali", "roll_number": 23, "age": 21, "email": "ali@gmail.com"},
    ).json()
    r = client.put(
        f"/students/{created['id']}",
        json={"email": "new@gmail.com"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "new@gmail.com"
    assert r.json()["name"] == "Ali"


def test_delete_student():
    created = client.post(
        "/students",
        json={"name": "Ali", "roll_number": 23, "age": 21, "email": "ali@gmail.com"},
    ).json()
    r = client.delete(f"/students/{created['id']}")
    assert r.status_code == 200
    r2 = client.get(f"/students/{created['id']}")
    assert r2.status_code == 404


def test_validation_age():
    r = client.post(
        "/students",
        json={"name": "X", "roll_number": 5, "age": 200, "email": "x@x.com"},
    )
    assert r.status_code == 422


def test_validation_email():
    r = client.post(
        "/students",
        json={"name": "X", "roll_number": 5, "age": 20, "email": "not-an-email"},
    )
    assert r.status_code == 422


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
