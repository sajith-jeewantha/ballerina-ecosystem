# Ballerina Knowledge Graph

Coverage map for the Ballerina SLM dataset. Each node in `nodes/` lists what training
data must cover (`must_cover`) and links to related nodes with typed edges.
The full specification lives in the shared spec doc (Ballerina Knowledge Graph — Specification v0.1).

## Quick start

```bash
pip install -e .
python -m ballerina_graph validate nodes/          # all validation rules
python -m ballerina_graph stats nodes/             # counts by type, priority, relation
python -m ballerina_graph export nodes/ --out build/   # build/graph.json + schema/node.schema.json
python -m ballerina_graph view nodes/               # build/viewer.html - open in any browser
python -m ballerina_graph serve nodes/              # local viewer with title editing (writes the YAML files)
```

## For the harness team

```python
from ballerina_graph import load_graph
g = load_graph("nodes/")
for node, item in g.iter_items():
    ref = g.ref(node, item)          # e.g. "lib.http#client.resilience" -> put in each sample's `covers`
for edge in g.edges(rel="uses"):
    edge.source_items, edge.target_items   # Item objects scoped by via / target_items
```

Install pinned: `pip install "ballerina-graph @ git+https://<git-host>/<org>/ballerina-graph.git@v0.1.0"`

## Editor support

Point the VS Code YAML extension at the schema by adding this to `.vscode/settings.json`:

```json
{ "yaml.schemas": { "./schema/node.schema.json": "nodes/*.yaml" } }
```

## Status

v3: 242 nodes (51 concept, 71 library, 69 connector, 6 trigger, 27 tool, 4 platform, 14 topic), 3,257 `must_cover` items and 1,704 edges, schema v0.2. Every Ballerina Central package (856), every Ballerina by Example program (592) and every Learn page (77) is covered. All nodes are `status: draft` and await domain-expert review, except the three deprecated packages (`lib.regex`, `lib.xmldata`, `lib.yaml`).
