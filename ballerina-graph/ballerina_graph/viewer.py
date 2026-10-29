"""Build a self-contained HTML viewer for the graph (no server needed)."""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from .loader import Graph
from .models import SCHEMA_VERSION

PLACEHOLDER = "/*__GRAPH_DATA__*/"


def render_viewer(graph: Graph, editable: bool = False) -> str:
    """editable=True turns on title editing, which needs the local `serve` API."""
    template = resources.files(__package__).joinpath("viewer_template.html").read_text(encoding="utf-8")
    data = {"schema_version": SCHEMA_VERSION, **graph.to_json()}
    if editable:
        data["editable"] = True
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return template.replace(PLACEHOLDER, payload)


def write_viewer(graph: Graph, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_viewer(graph), encoding="utf-8")
    return p
