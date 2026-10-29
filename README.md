# Ballerina Ecosystem Knowledge Graph

A knowledge graph of the Ballerina language and its ecosystem that drives supervised
fine-tuning (SFT) dataset generation. Each node lists what the training data must cover
(`must_cover` items), and typed edges link related nodes. Every `must_cover` item becomes one or
more training samples, so a feature missing from the graph is never trained on.

The nodes are built from:
- the [Ballerina Language Specification 2024R1](https://ballerina.io/spec/lang/2024R1/)
  (language concepts and the lang library)
- the module READMEs and API sources in the
  [ballerina-platform](https://github.com/orgs/ballerina-platform/repositories) GitHub org
- [Ballerina by Example](https://ballerina.io/learn/by-example/)
- [Ballerina Central](https://central.ballerina.io/ballerina-library)
- the [Learn](https://ballerina.io/learn/) docs (tools, packages, guides)

Every node cites the pages it was built from in its `sources`.

**View the graph:** https://sajith-jeewantha.github.io/ballerina-ecosystem/ballerina-graph/build/viewer.html
(raw data: [graph.json](https://sajith-jeewantha.github.io/ballerina-ecosystem/ballerina-graph/build/graph.json))

## Repository layout

```
.
├── README.md                 # this file
├── prompt.md                 # task brief used to build the spec-derived nodes
└── ballerina-graph/          # Python package: schema, loader, CLI and node data
    ├── ballerina_graph/      # Pydantic models, loader/validator, export and viewer
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
so they stay in sync. To get an image of the graph, use the viewer's **Download PNG** button.

### Using the viewer

- **Spacing:** the Spacing control above the graph changes the gap between nodes (`−`/`+` or
  the slider, 0.5× to 3×). **Default** resets it to 2.0×. Your last setting is remembered in
  the browser.
- **Download PNG:** saves the whole graph (every node that passes the current filters, not just
  the part on screen) as `ballerina-graph.png`, at a size where labels stay readable.
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
| Nodes | 159: 50 concept, 79 library, 20 tool, 10 topic |
| `must_cover` items | 2,054 |
| Edges | 1,088 (uses 912, requires 109, related 37, part_of 13, implements 11, alternative_to 4, counterpart_of 2) |
| Priority | core 43, important 76, long_tail 40 |

`validate` reports `OK: 159 nodes, 2054 items, 1088 edges, 0 warning(s)`.

What the nodes cover:

| Type | Nodes | Scope |
|---|---|---|
| `concept` | 50 | Language features from spec 2024R1 chapters 2 to 10 (types, expressions, statements, concurrency, XML, queries, transactions...) |
| `library` | 79 | The lang library (`langlib` and 13 `ballerina/lang.*` modules); the `ballerina/*` standard library (HTTP, GraphQL, gRPC, WebSocket, SQL, persist, IO, data.*, auth, JWT, OAuth2, crypto, log, test, observe, AI, MCP...); key `ballerinax/*` connectors (MySQL, PostgreSQL, MSSQL, Oracle, JDBC, MongoDB, Redis, Kafka, RabbitMQ, NATS, JMS, IBM MQ, Azure Service Bus, AI model providers, Pinecone) |
| `tool` | 20 | `bal` and its subcommands, packages, `Ballerina.toml`, `Dependencies.toml`, `Config.toml`, Ballerina Central, testing, code generators (OpenAPI, GraphQL, gRPC, AsyncAPI, persist, bindgen, WSDL, EDI), Code to Cloud, GraalVM, VS Code |
| `topic` | 10 | Cross-cutting guides: REST APIs, best practices, data mapping, integration patterns, AI agents, security, observability, connectors, event-driven, resiliency |

Library titles are the package names you import (`ballerina/http`, `ballerinax/mysql`).
SaaS connectors (Salesforce, GitHub, Slack...) are not included yet.
