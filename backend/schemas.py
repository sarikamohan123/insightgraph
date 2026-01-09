from pydantic import BaseModel


class Node(BaseModel):
    id: str
    label: str
    type: str
    confidence: float = 0.0


class Edge(BaseModel):
    source: str
    target: str
    relation: str


class ExtractResponse(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
