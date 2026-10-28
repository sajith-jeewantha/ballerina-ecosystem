"""CLI: python -m ballerina_graph {validate,export,stats} NODES_DIR"""
from __future__ import annotations
import argparse
import sys
from collections import Counter
from pathlib import Path

from .export import write_graph_json, write_schema
from .viewer import write_viewer
from .loader import GraphValidationError, load_graph


def _load(nodes_dir: str):
    try:
        return load_graph(nodes_dir)
    except GraphValidationError as exc:
        print(f"FAILED: {len(exc.errors)} error(s)")
        for e in exc.errors:
            print(f"  error   {e}")
        for w in exc.warnings:
            print(f"  warning {w}")
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="ballerina_graph")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="validate all node files")
    v.add_argument("nodes_dir")
    ex = sub.add_parser("export", help="write graph.json and node.schema.json")
    ex.add_argument("nodes_dir")
    ex.add_argument("--out", default="build")
    ex.add_argument("--schema-out", default="schema/node.schema.json")
    vw = sub.add_parser("view", help="write a self-contained HTML viewer")
    vw.add_argument("nodes_dir")
    vw.add_argument("--out", default="build/viewer.html")
    st = sub.add_parser("stats", help="print counts")
    st.add_argument("nodes_dir")
    args = ap.parse_args(argv)

    g = _load(args.nodes_dir)
    if args.cmd == "validate":
        for w in g.warnings:
            print(f"  warning {w}")
        print(f"OK: {len(g.nodes)} nodes, {sum(len(n.must_cover) for n in g.nodes.values())} items, "
              f"{len(g.edges())} edges, {len(g.warnings)} warning(s)")
    elif args.cmd == "export":
        gp = write_graph_json(g, Path(args.out) / "graph.json")
        sp = write_schema(args.schema_out)
        print(f"wrote {gp} and {sp}")
    elif args.cmd == "view":
        vp = write_viewer(g, args.out)
        print(f"wrote {vp} - open it in a browser")
    elif args.cmd == "stats":
        nodes = list(g.nodes.values())
        print(f"nodes: {len(nodes)}")
        print("  by type:     " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(n.type for n in nodes).items())))
        print("  by priority: " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(n.priority for n in nodes).items())))
        print(f"items: {sum(len(n.must_cover) for n in nodes)}")
        edges = g.edges()
        print(f"edges: {len(edges)}")
        print("  by relation: " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(e.rel for e in edges).items())))


if __name__ == "__main__":
    main()
