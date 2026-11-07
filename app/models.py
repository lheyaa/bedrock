"""Request and response shapes for the Bedrock API."""

from typing import Literal, Optional 

from pydantic import BaseModel, Field

Kind = Literal["claim", "assumption", "axiom", "evidence"]

class NodeCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    kind: Kind = "assumption"
    note: str = ""
    parent_id: Optional[str] = None

class NodeUpdate(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1, max_length=500)
    kind: Optional[Kind] = None
    note: Optional[str] = None

class Node(BaseModel):
    id: str
    text: str
    kind: Kind
    note: str
    parent_id: Optional[str]
    created_at: str

    