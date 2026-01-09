# C:\Sarika\repos\insightgraph\backend\tests\test_extractor.py

from backend.extractor import extract_graph


def test_extract_nodes_python_and_data_science():
    text = "Python is used for data science"
    result = extract_graph(text)

    ids = sorted([n.id for n in result.nodes])
    assert "python" in ids
    assert "data-science" in ids


def test_extract_creates_one_edge_used_for():
    text = "Python is used for data science"
    result = extract_graph(text)

    # We expect EXACTLY 1 edge (this will fail if duplicates still happen)
    assert len(result.edges) == 1
    edge = result.edges[0]
    assert edge.source == "python"
    assert edge.target == "data-science"
    assert edge.relation == "used_for"


def test_no_edge_if_only_one_node_found():
    text = "I like python"
    result = extract_graph(text)

    assert len(result.nodes) == 1
    assert len(result.edges) == 0


def test_no_nodes_if_text_has_no_known_terms():
    text = "I love cooking and hiking"
    result = extract_graph(text)

    assert len(result.nodes) == 0
    assert len(result.edges) == 0


def test_no_duplicate_edges():
    text = "Python is used for data science"
    result = extract_graph(text)

    # turn edges into tuples so we can compare unique vs total
    tuples = [(e.source, e.target, e.relation) for e in result.edges]

    assert len(tuples) == len(set(tuples))


def test_confidence_increases_with_frequency():
    text = "Python is great. Python is used for data science."
    result = extract_graph(text)

    python_node = next(n for n in result.nodes if n.id == "python")
    assert python_node.confidence == 0.9
