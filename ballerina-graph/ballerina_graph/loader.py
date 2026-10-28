"""Load and validate a directory of node YAML files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal, Optional

import yaml
from pydantic import ValidationError

from .models import SYMMETRIC_RELATIONS, Edge, Item, Node, Source

SPLIT_WARNING_THRESHOLD = 20


class GraphValidationError(Exception):
    def __init__(self, errors: list[str], warnings: list[str] | None = None):
        self.errors = errors
        self.warnings = warnings or []
        super().__init__(f"{len(errors)} validation error(s):\n  - " + "\n  - ".join(errors))


@dataclass(frozen=True)
class ResolvedEdge:
    source: Node
    target: Node
    rel: str
    edge: Edge
    source_items: list[Item]   # items named in `via`, or all source items when empty
    target_items: list[Item]   # items named in `target_items`, or all target items when empty

    @property
    def is_scoped(self) -> bool:
        return bool(self.edge.via or self.edge.target_items)


class Graph:
    def __init__(self, nodes: dict[str, Node], warnings: list[str]):
        self.nodes = nodes
        self.warnings = warnings

    # --- items -------------------------------------------------------------
    @staticmethod
    def ref(node: Node, item: Item) -> str:
        return f"{node.id}#{item.id}"

    def iter_items(self, include_retired: bool = False) -> Iterator[tuple[Node, Item]]:
        for node in self.nodes.values():
            if node.status == "deprecated" and not include_retired:
                continue
            for item in node.must_cover:
                if item.replaced_by and not include_retired:
                    continue
                yield node, item

    def resolve(self, ref: str) -> tuple[Node, Optional[Item]]:
        node_id, _, item_id = ref.partition("#")
        node = self.nodes[node_id]
        return node, (node.item(item_id) if item_id else None)

    def sources_for(self, node: Node, item: Optional[Item] = None) -> list[Source]:
        if item is not None and item.sources:
            return list(item.sources)
        return list(node.sources)

    # --- edges -------------------------------------------------------------
    def edges(self, rel: Optional[str] = None) -> list[ResolvedEdge]:
        out = []
        for node in self.nodes.values():
            for e in node.edges:
                if rel is not None and e.rel != rel:
                    continue
                target = self.nodes[e.to]
                src_items = [node.item(i) for i in e.via] or list(node.must_cover)
                dst_items = [target.item(i) for i in e.target_items] or list(target.must_cover)
                out.append(ResolvedEdge(node, target, e.rel, e, src_items, dst_items))
        return out

    def neighbors(
        self,
        node_id: str,
        rel: Optional[str] = None,
        direction: Literal["out", "in", "both"] = "both",
    ) -> list[Node]:
        result: dict[str, Node] = {}
        for re_ in self.edges(rel):
            symmetric = re_.rel in SYMMETRIC_RELATIONS
            if re_.source.id == node_id and (direction in ("out", "both") or symmetric):
                result[re_.target.id] = re_.target
            if re_.target.id == node_id and (direction in ("in", "both") or symmetric):
                result[re_.source.id] = re_.source
        return list(result.values())

    # --- export ------------------------------------------------------------
    def to_json(self) -> dict:
        return {
            "nodes": [n.model_dump(mode="json", exclude_none=True) for n in self.nodes.values()],
            "edges": [
                {
                    "source": n.id,
                    "target": e.to,
                    "rel": e.rel,
                    "via": list(e.via),
                    "target_items": list(e.target_items),
                    **({"note": e.note} if e.note else {}),
                }
                for n in self.nodes.values()
                for e in n.edges
            ],
        }


def _read_nodes(path: Path, errors: list[str]) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    files = sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml"))
    if not files:
        errors.append(f"no node files found in {path}")
    for f in files:
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{f.name}: YAML parse error: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{f.name}: file must contain one mapping (one node)")
            continue
        try:
            node = Node.model_validate(data)
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"]) or "<node>"
                errors.append(f"{f.name}: {loc}: {err['msg']}")
            continue
        if f.stem != node.id:
            errors.append(f"{f.name}: file name must be '{node.id}.yaml'")
        if node.id in nodes:
            errors.append(f"{f.name}: duplicate node id '{node.id}'")
            continue
        nodes[node.id] = node
    return nodes


def _find_cycle(nodes: dict[str, Node], rel: str) -> Optional[list[str]]:
    adj = {nid: [e.to for e in n.edges if e.rel == rel and e.to in nodes] for nid, n in nodes.items()}
    WHITE, GREY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in nodes}
    stack: list[str] = []

    def dfs(u: str) -> Optional[list[str]]:
        color[u] = GREY
        stack.append(u)
        for v in adj[u]:
            if color[v] == GREY:
                return stack[stack.index(v):] + [v]
            if color[v] == WHITE:
                found = dfs(v)
                if found:
                    return found
        stack.pop()
        color[u] = BLACK
        return None

    for nid in nodes:
        if color[nid] == WHITE:
            found = dfs(nid)
            if found:
                return found
    return None


def validate_graph(nodes: dict[str, Node]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    symmetric_seen: dict[tuple[str, frozenset[str]], str] = {}
    degree = {nid: 0 for nid in nodes}

    for node in nodes.values():
        pairs: set[tuple[str, str]] = set()
        if node.replaced_by and node.replaced_by not in nodes:
            errors.append(f"{node.id}: replaced_by points to unknown node '{node.replaced_by}'")
        for e in node.edges:
            where = f"{node.id} -[{e.rel}]-> {e.to}"
            if e.to == node.id:
                errors.append(f"{where}: self-edge")
                continue
            if e.to not in nodes:
                errors.append(f"{where}: target node does not exist")
                continue
            if (e.to, e.rel) in pairs:
                errors.append(f"{where}: duplicate edge")
            pairs.add((e.to, e.rel))
            if e.rel in SYMMETRIC_RELATIONS:
                key = (e.rel, frozenset({node.id, e.to}))
                if key in symmetric_seen:
                    errors.append(f"{where}: symmetric edge already declared on {symmetric_seen[key]}")
                symmetric_seen[key] = node.id
            for i in e.via:
                if i not in node.item_ids:
                    errors.append(f"{where}: via '{i}' is not an item of {node.id}")
            target = nodes[e.to]
            for i in e.target_items:
                if i not in target.item_ids:
                    errors.append(f"{where}: target_items '{i}' is not an item of {e.to}")
            if e.rel in ("uses", "implements") and not (e.via or e.target_items):
                warnings.append(f"{where}: unscoped {e.rel} edge (no via / target_items)")
            degree[node.id] += 1
            degree[e.to] += 1

    cycle = _find_cycle(nodes, "requires")
    if cycle:
        errors.append("requires cycle: " + " -> ".join(cycle))

    for node in nodes.values():
        if degree[node.id] == 0:
            warnings.append(f"{node.id}: orphan node (no edges in or out)")
        if len(node.must_cover) > SPLIT_WARNING_THRESHOLD:
            warnings.append(f"{node.id}: {len(node.must_cover)} items; consider splitting")
        if not node.sources and not any(it.sources for it in node.must_cover):
            warnings.append(f"{node.id}: no sources on node or items")
    return errors, warnings


def load_graph(path: str | Path, strict: bool = True) -> Graph:
    """Load every node file in `path` and validate the graph.

    strict=True raises GraphValidationError if any error is found.
    Warnings are always available on `Graph.warnings`.
    """
    errors: list[str] = []
    nodes = _read_nodes(Path(path), errors)
    graph_errors, warnings = validate_graph(nodes)
    errors.extend(graph_errors)
    if errors and strict:
        raise GraphValidationError(errors, warnings)
    return Graph(nodes, warnings)
