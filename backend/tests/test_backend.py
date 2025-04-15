import pytest
import sys
import os

# Kept getting Module Not Found for backend, this is what worked
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
from backend.api import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def test_top_professors_snapshot(snapshot, client):
    response = client.get("/api/v1/top_professors?course_id=1")
    assert response.status_code == 200
    snapshot.assert_match(
        json.dumps(response.get_json(), indent=2, sort_keys=True),
        "top_professors_response",
    )


@pytest.mark.parametrize(
    "params, snapshot_name",
    [
        ({"credits": 4, "class_level": 100, "department_id": 1}, "top_classes_basic"),
        (
            {"credits": 4, "class_level": 100, "department_id": 2, "ucore": 3},
            "top_classes_with_ucore",
        ),
        (
            {"credits": 3, "class_level": 100, "department_id": 999},
            "top_classes_invalid_dept",
        ),
        ({"class_level": 100, "department_id": 1}, "top_classes_missing_credits"),
    ],
)
def test_top_class_snapshot(snapshot, client, params, snapshot_name):
    response = client.get("/api/v1/top_classes", query_string=params)
    assert response.status_code == 200
    snapshot.assert_match(
        json.dumps(response.get_json(), indent=2, sort_keys=True), snapshot_name
    )
