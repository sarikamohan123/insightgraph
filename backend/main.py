from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="InsightGraph API")


class ExtractRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
def extract(req: ExtractRequest):
    return {
        "nodes": [
            {"id": "python", "label": "Python", "type": "Tech"},
            {"id": "data-science", "label": "Data Science", "type": "Concept"},
        ],
        "edges": [
            {"source": "python", "target": "data-science", "relation": "used_for"}
        ],
    }
