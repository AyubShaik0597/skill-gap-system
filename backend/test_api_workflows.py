
import os
from pathlib import Path

# Isolated test database and test-only JWT secret.
TEST_DB = Path(__file__).with_name("skillpath_test.sqlite")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-secret-key-never-use-in-production-123456789",
)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.main import app
from app.seed_demo import seed
from app.models import User
from app.security.utils import hash_password


TEST_EMAIL = "test-admin@example.com"
TEST_PASSWORD = "TestAdminPassword123!"


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def admin_headers(client):
    """Create a test Admin, log in, and return its JWT headers."""
    with Session(engine) as db:
        user = User(
            email=TEST_EMAIL,
            full_name="Test Administrator",
            password_hash=hash_password(TEST_PASSWORD),
            role="Admin",
            employee_id=None,
            is_active=True,
        )
        db.add(user)
        db.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_and_dashboard():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "healthy"

        headers = admin_headers(client)
        response = client.get(
            "/api/dashboard/summary", headers=headers
        )
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["employees"] == 1
        assert data["skills"] == 6
        assert data["courses"] == 3


def test_gap_and_recommendation_endpoints():
    with TestClient(app) as client:
        headers = admin_headers(client)

        gaps = client.get(
            "/api/employees/1/gaps", headers=headers
        )
        assert gaps.status_code == 200, gaps.text
        assert gaps.json()["gap_count"] > 0

        recommendations = client.get(
            "/api/employees/1/recommendations?diagnostics=true",
            headers=headers,
        )
        assert recommendations.status_code == 200, recommendations.text
        assert "recommendations" in recommendations.json()
        assert "rejected_courses" in recommendations.json()


def test_enrollment_duplicate_completion_and_reassessment():
    with TestClient(app) as client:
        headers = admin_headers(client)

        created = client.post(
            "/api/enrollments",
            json={"employee_id": 1, "course_id": 1, "actor": "pytest"},
            headers=headers,
        )
        assert created.status_code == 200, created.text
        enrollment_id = created.json()["id"]

        duplicate = client.post(
            "/api/enrollments",
            json={"employee_id": 1, "course_id": 1, "actor": "pytest"},
            headers=headers,
        )
        assert duplicate.status_code == 409, duplicate.text

        completed = client.post(
            f"/api/enrollments/{enrollment_id}/complete",
            json={
                "score": 90,
                "outcome": "PASSED",
                "actor": "pytest",
            },
            headers=headers,
        )
        assert completed.status_code == 200, completed.text

        duplicate_completion = client.post(
            f"/api/enrollments/{enrollment_id}/complete",
            json={
                "score": 90,
                "outcome": "PASSED",
                "actor": "pytest",
            },
            headers=headers,
        )
        assert duplicate_completion.status_code == 409, duplicate_completion.text

        assessment = client.post(
            "/api/employees/1/skills/1/assessments",
            json={
                "level": 4,
                "assessor": "pytest",
                "source": "MANUAL",
                "notes": "test reassessment",
            },
            headers=headers,
        )
        assert assessment.status_code == 200, assessment.text

        history = client.get(
            "/api/employees/1/assessments", headers=headers
        )
        assert history.status_code == 200, history.text
        assert any(row["skill"] == "Python" for row in history.json())


def test_learning_path_and_audit_endpoints():
    with TestClient(app) as client:
        headers = admin_headers(client)

        path = client.post(
            "/api/employees/1/learning-paths",
            headers=headers,
        )
        assert path.status_code in (200, 400, 422), path.text

        if path.status_code == 200:
            paths = client.get(
                "/api/employees/1/learning-paths",
                headers=headers,
            )
            assert paths.status_code == 200, paths.text
            assert len(paths.json()) >= 1

        audit = client.get("/api/audit-events", headers=headers)
        assert audit.status_code == 200, audit.text
        assert isinstance(audit.json(), list)


def test_nonexistent_employee_returns_404():
    with TestClient(app) as client:
        headers = admin_headers(client)
        response = client.get(
            "/api/employees/999999/gaps",
            headers=headers,
        )
        assert response.status_code == 404, response.text


def test_protected_endpoints_reject_anonymous_requests():
    with TestClient(app) as client:
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 401, response.text

        response = client.get("/api/employees/1/gaps")
        assert response.status_code == 401, response.text
