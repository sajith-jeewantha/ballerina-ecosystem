"""Exports: JSON Schema for editors/viewers and graph.json for the viewer."""
from __future__ import annotations

import json
from pathlib import Path

from .loader import Graph
from .models import SCHEMA_VERSION, Node


def node_json_schema() -> dict:
    schema = Node.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"ballerina-graph/node.schema.v{SCHEMA_VERSION}.json"
    schema["title"] = "Ballerina Knowledge Graph node"
    return schema


def write_schema(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(node_json_schema(), indent=2) + "\n", encoding="utf-8")
    return p


def write_graph_json(graph: Graph, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": SCHEMA_VERSION, **graph.to_json()}
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p
