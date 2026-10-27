"""
Unit tests for the Inventory microservice.
"""
import pytest
from src.app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "inventory-api"
    assert data["status"] == "operational"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_get_items(client):
    response = client.get("/items")
    assert response.status_code == 200
    data = response.get_json()
    assert "items" in data
    assert data["count"] >= 2


def test_add_item_success(client):
    new_item = {"name": "Widget C", "quantity": 15}
    response = client.post("/items", json=new_item)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Widget C"
    assert data["quantity"] == 15
    assert "id" in data


def test_add_item_validation_error(client):
    # Missing quantity
    res1 = client.post("/items", json={"name": "Bad Widget"})
    assert res1.status_code == 400
    assert "error" in res1.get_json()

    # Negative quantity
    res2 = client.post("/items", json={"name": "Bad Widget", "quantity": -5})
    assert res2.status_code == 400

    # Missing name
    res3 = client.post("/items", json={"quantity": 10})
    assert res3.status_code == 400


def test_ledger_endpoint(tmp_path):
    from scripts.build_ledger import build_ledger
    out_dir = tmp_path / "public"
    build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(tmp_path / "nonexistent.json"),
        repo_dir=".",
        project_title="Test Accountability Ledger",
    )
    app = create_app({"TESTING": True, "LEDGER_DIR": str(out_dir)})
    with app.test_client() as test_client:
        response = test_client.get("/ledger")
        assert response.status_code == 200
        assert b"Accountability Ledger" in response.data

def test_inventory_summary_endpoint(client):
    response = client.get("/inventory/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_items"] >= 2
    assert data["total_quantity"] > 0
