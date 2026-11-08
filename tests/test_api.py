"""Tests for the Bedrock API."""

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Point the app at an empty throwaway database for every test."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    yield


def test_list_is_empty_initially():
    response = client.get("/api/nodes")
    assert response.status_code == 200
    assert response.json() == []


def test_create_returns_201_and_the_node():
    response = client.post("/api/nodes", json={"text": "Word of mouth wins"})
    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "Word of mouth wins"
    assert body["kind"] == "assumption"
    assert body["parent_id"] is None
    assert body["id"]


def test_partial_update_leaves_other_fields_alone():
    created = client.post("/api/nodes", json={"text": "Original text"}).json()
    response = client.patch(f"/api/nodes/{created['id']}", json={"kind": "axiom"})
    assert response.status_code == 200
    assert response.json()["kind"] == "axiom"
    assert response.json()["text"] == "Original text"


def test_update_unknown_node_returns_404():
    response = client.patch("/api/nodes/nonsense", json={"kind": "axiom"})
    assert response.status_code == 404


def test_delete_removes_descendants():
    parent = client.post("/api/nodes", json={"text": "Parent"}).json()
    client.post("/api/nodes", json={"text": "Child", "parent_id": parent["id"]})
    assert len(client.get("/api/nodes").json()) == 2

    response = client.delete(f"/api/nodes/{parent['id']}")
    assert response.status_code == 204
    assert client.get("/api/nodes").json() == []


def test_delete_unknown_node_returns_404():
    assert client.delete("/api/nodes/nonsense").status_code == 404


def test_invalid_kind_is_rejected():
    response = client.post("/api/nodes", json={"text": "Bad", "kind": "banana"})
    assert response.status_code == 422


def test_create_with_unknown_parent_returns_404():
    response = client.post(
        "/api/nodes", json={"text": "Orphan", "parent_id": "nonsense"}
    )
    assert response.status_code == 404


def test_tree_nests_children():
    parent = client.post("/api/nodes", json={"text": "Parent"}).json()
    client.post("/api/nodes", json={"text": "Child", "parent_id": parent["id"]})

    tree = client.get("/api/tree").json()
    assert len(tree) == 1
    assert tree[0]["text"] == "Parent"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["text"] == "Child"