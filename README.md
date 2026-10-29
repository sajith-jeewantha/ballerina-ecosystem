# Ballerina Ecosystem Knowledge Graph

A knowledge graph of the Ballerina language that drives supervised fine-tuning (SFT) dataset
generation. Each node lists what the training data must cover (`must_cover` items), and typed
edges link related nodes. Every `must_cover` item becomes one or more training samples, so a
feature missing from the graph is never trained on.

The current nodes are built from the
[Ballerina Language Specification 2024R1](https://ballerina.io/spec/lang/2024R1/).

**View the graph:** https://sajith-jeewantha.github.io/ballerina-ecosystem/ballerina-graph/build/viewer.html
(raw data: [graph.json](https://sajith-jeewantha.github.io/ballerina-ecosystem/ballerina-graph/build/graph.json))

## Repository layout

```
.
├── README.md                 # this file
├── prompt.md                 # task brief used to build the spec-derived nodes
└── ballerina-graph/          # Python package: schema, loader/validator, export and viewer CLI and node data
    ├── nodes/                # one YAML file per node (<id>.yaml)
    ├── schema/               # node.schema.json for editor validation
    ├── pyproject.toml
    └── README.md             # package README and harness API
```

## Setup

Requires Python 3.10 or later.

```bash
cd ballerina-graph
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commands

Run these from `ballerina-graph/`:

| Command | What it does |
|---|---|
| `python -m ballerina_graph validate nodes/` | Runs all validation rules. Errors fail the run; warnings are printed. |
| `python -m ballerina_graph stats nodes/` | Prints counts by node type, priority and edge relation. |
| `python -m ballerina_graph export nodes/ --out build/` | Writes `build/graph.json` and regenerates `schema/node.schema.json`. |
| `python -m ballerina_graph view nodes/` | Writes `build/viewer.html`, a self-contained graph viewer you can open in any browser. |
| `python -m ballerina_graph serve nodes/ [--port 8000]` | Serves the viewer at http://127.0.0.1:8000/ with title editing turned on. |

`build/` holds the published graph: `build/graph.json` (the full graph) and
`build/viewer.html` (the interactive viewer). Re-run `export` and `view` after changing nodes
so they stay in sync.

### Using the viewer

- **Spacing:** the Spacing control above the graph changes the gap between nodes (`−`/`+` or
  the slider, 0.5× to 3×). **Default** resets it to 1.5×. Your last setting is remembered in
  the browser.
- **Full screen:** **Full screen** shows only the graph across the whole screen. Click
  **Exit full screen** or press Esc to return.
- **Editing titles:** run `serve`, open a node and click **Edit title**. Saving rewrites only
  the `title:` line in that node's YAML file. Enter saves and Esc cancels. Editing is not
  available on GitHub Pages or in `build/viewer.html`, which have no server to write files.
  After editing, re-run `view` and `export` to update `build/`.

GitHub Pages serves the `main` branch, so pushing updated `build/` files to `main` updates the
hosted viewer.

## Node format

Each node is a YAML file in `ballerina-graph/nodes/` named after its id, for example
`concept.arrays_tuples.yaml`:

```yaml
schema_version: "0.1"
id: concept.arrays_tuples
type: concept            # concept | library | tool | topic
title: Arrays and tuples
summary: ...
priority: core           # core | important | long_tail
status: draft
sources:
  - {url: "https://ballerina.io/spec/lang/2024R1/#section_5.4.1", kind: spec, note: "5.4.1 Lists"}
must_cover:
  - id: array_basics
    text: Declare arrays with `T[]`, build them with list constructors ...
    difficulty: [beginner]
out_of_scope:
  - "List binding patterns and destructuring (concept.binding_patterns)"
edges:
  - {to: concept.basic_types, rel: requires}
  - {to: concept.langlib, rel: uses, via: [array_langlib], target_items: [lang_array]}
```

Node types and id prefixes:

| Type | Prefix | Covers |
|---|---|---|
| `concept` | `concept.` | Language features defined by the spec, including the lang library |
| `library` | `lib.` | Standard-library and connector modules, such as `ballerina/http` |
| `tool` | `tool.` | The `bal` CLI and tooling |
| `topic` | `topic.` | Cross-cutting guidance such as idioms and best practices |

### Authoring rules

- Each node has 5 to 20 `must_cover` items. Each item starts with a verb and names real syntax.
- Items must come from the source. For spec nodes, cite spec anchors with `kind: spec`.
- `requires` edges must not form a cycle.
- `uses` and `implements` edges should be scoped with `via` (source items) and, where useful,
  `target_items`.
- Symmetric relations (`related`, `alternative_to`, `counterpart_of`) are declared once, on one
  of the two nodes.
- Edges must not point to missing nodes, and every node should have at least one edge in or out.

## Current status

All nodes are `status: draft` and await domain-expert review.

| | Count |
|---|---|
| Nodes | 69 (all `concept`) |
| `must_cover` items | 849 |
| Edges | 266 (requires 96, uses 144, related 14, part_of 10, counterpart_of 1, implements 1) |
| Priority | core 32, important 31, long_tail 6 |

`validate` reports `OK: 69 nodes, 849 items, 266 edges, 0 warning(s)`.

The nodes cover spec chapters 2 to 11. Library, tool and topic nodes are not yet included,
because the spec does not define the standard library or tooling.
