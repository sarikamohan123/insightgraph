from fastapi import FastAPI
from pydantic import BaseModel

from schemas import Node, Edge, ExtractResponse
from extractor import extract_graph

app = FastAPI(title="InsightGraph API")


class ExtractRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):
    return extract_graph(req.text)

    
