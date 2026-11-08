"""HHTP API for Bedrock. Translates requests into store calls."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import store
from app.db import init_db
from app.models import Node, NodeCreate, NodeUpdate

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run once at startup: make sure the schema exists."""
    init_db()
    yield

app = FastAPI(title="Bedrock", lifespan=lifespan)

@app.get("/api/nodes", response_model=list[Node])
def read_nodes():
    return store.list_nodes()

@app.post("/api/nodes", response_model=Node, status_code=201)
def add_node(payload: NodeCreate):
    if payload.parent_id is not None and store.get_node(payload.parent_id) is None:
        raise HTTPException(status_code=404, detail="Parent node not found")
    return store.create_node(
        text=payload.text,
        kind=payload.kind, 
        note=payload.note,
        parent_id=payload.parent_id,
    )

@app.patch("/api/nodes/{node_id}", response_model=Node)
def edit_node(node_id: str, payload: NodeUpdate):
    updated = store.update_node(node_id, payload.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return updated

@app.delete("/api/nodes/{node_id}", status_code=204)
def remove_node(node_id: str):
    if not store.delete_node(node_id):
        raise HTTPException(status_code=404, detail="Node not found")

@app.get("/api/tree")
def read_tree():
    return store.build_tree(store.list_nodes())

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")