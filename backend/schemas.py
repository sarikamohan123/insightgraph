from pydantic import BaseModel
from typing import List

class Node(BaseModel):
    id: str
    label: str
    type: str
    confidence: float =0.0

class Edge(BaseModel):
    source: str
    target: str
    relation: str

class ExtractResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    