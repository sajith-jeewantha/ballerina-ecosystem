# Task: Build the Ballerina language knowledge graph from the language spec

## Context
I'm building a knowledge graph of the Ballerina language. It will drive supervised fine-tuning (SFT) dataset generation: every `must_cover` item in every node becomes one or more training samples. If a feature is missing from the graph, the model is never trained on it. **Coverage and accuracy matter more than anything else.**

Project: `./ballerina-graph` (Python, Pydantic schema v0.1).
Source of truth: Ballerina Language Specification 2024R1: https://ballerina.io/spec/lang/2024R1/

## Rules
- **Read-only on code.** Don't modify anything in `ballerina-graph/` except the `nodes/` folder. Don't touch `ballerina_graph/`, `schema/`, `pyproject.toml` or `README.md`.
- **No invention.** Every `must_cover` item must be something the 2024R1 spec actually defines. Don't add features from other spec versions, blogs or memory. If you're unsure whether something is in 2024R1, leave it out and list it in your final report.
- Don't run `export` or `view`. They write to `build/` and `schema/`. Only `validate` and `stats` are allowed.

## Step 1: Understand the project (before researching)
Read these files fully:
- `ballerina_graph/models.py`: node schema (the source of truth)
- `ballerina_graph/loader.py`: validation rules
- `schema/node.schema.json`, `README.md`
- `nodes/concept.arrays_tuples.yaml`: style reference for one node

## Step 2: Read the whole spec and build an inventory
The spec is long. Read it section by section, including every subsection, the lang library section and the appendices. Don't stop at the table of contents.

Before writing any YAML, build an inventory: a list of every spec section/subsection and the node that will cover it. Every section that defines a language feature must map to a node. Sections that are pure notation or front matter may map to "none", with a reason. Keep this inventory, because you'll reuse it in Step 5.

## Step 3: Design the nodes
**Granularity**
- One node = one coherent topic that a learner would study as a unit (e.g. "Arrays and tuples", "Query expressions", "Error handling", "Transactions").
- Aim for 5–20 `must_cover` items per node. The validator warns above 20, so split such a node into sub-nodes (e.g. `concept.query_expressions` and `concept.query_joins_grouping`) linked with `part_of`.
- Don't create one node per grammar production. Group them sensibly, but make sure every production that matters for writing code is reachable from some item.

**Node fields**
- `schema_version: "0.1"`, `type: concept`, `status: draft`
- `id`: `concept.<snake_case>`. The file name must be exactly `<id>.yaml`.
- `title`, and a one-sentence `summary`
- `priority`:
  - `core`: everyday code (types, variables, functions, control flow, errors, records/maps, arrays, objects, queries)
  - `important`: common but not daily (concurrency/workers, transactions, XML, tables, streams, isolation, services/listeners)
  - `long_tail`: rarely written by hand (lexical details, Unicode escapes, obscure abstract operations, metadata minutiae)
- `sources`: link to the **specific spec section anchor** you read (open the page and copy the real anchor; don't guess it) with `kind: spec`. Put item-level `sources` on items that come from a different section than the rest of the node.
- `out_of_scope`: features that are deliberately excluded, or that another node covers instead
- `notes`: reviewer-only remarks, e.g. ambiguities in the spec

**`must_cover` items**
- `id`: snake_case, unique within the node
- `text`: a **concrete, testable capability** starting with a verb (Declare / Use / Explain / Convert / Handle / Distinguish…), and naming the actual syntax, keywords or langlib functions. Example: "Use `check` and `checkpanic` to propagate or panic on error values", not "Error handling basics".
- Include edge cases and semantics the spec states explicitly: panics, type-narrowing rules, immutability, precision/overflow behaviour, evaluation order, and so on. These make high-value training samples.
- `difficulty`: a subset of `[beginner, intermediate, advanced]`. Omit it only if the item truly spans all three.

**Lang library**
Create `concept.langlib` with one item per lang module the 2024R1 spec defines. Use ids like `lang_array`, `lang_string`, `lang_map`, `lang_int` and so on: other nodes target these ids, and the sample node already references `concept.langlib#lang_array`. If a module needs detailed coverage, add a dedicated node (e.g. `concept.langlib_string`) with `part_of` → `concept.langlib`.

## Step 4: Add the edges
Allowed `rel` values and how to use them:
- `requires` (directed): you must understand the target first. **Must not form a cycle.**
- `uses` (directed): this node's items use the target's features. **Always scope it** with `via` (source item ids) and/or `target_items` (target item ids).
- `implements` (directed): this construct is a concrete form of the target. Scope it the same way as `uses`.
- `part_of` (directed): this is a sub-topic of the target node.
- `counterpart_of`, `alternative_to`, `related` (symmetric): **declare each pair once, on one node only.**

Hard rules (the validator fails on any of these):
- Every `to` target must exist as a node file. No dangling references. The sample node points to `concept.basic_types` and `concept.langlib`, so both must exist.
- Every id in `via` / `target_items` must be a real item id on that node.
- No self-edges, and no duplicate `(to, rel)` pairs on the same node.
- Every node must have at least one edge in or out (no orphans).

## Step 5: Write, validate and fix
1. Delete the existing YAML files in `ballerina-graph/nodes/` (currently only the sample `concept.arrays_tuples.yaml`). Recreate an arrays/tuples node in the same style, updated to the 2024R1 spec.
2. Write one YAML file per node into `ballerina-graph/nodes/`.
3. From `ballerina-graph/`, run:
   ```
   .venv/bin/python -m ballerina_graph validate nodes/
   .venv/bin/python -m ballerina_graph stats nodes/
   ```
4. Fix **every error and every warning**, and re-run until you get `OK` with 0 warnings. If a warning can't reasonably be fixed, explain it in the report.
5. Coverage check: walk through your Step 2 inventory and confirm that every spec section maps to at least one node/item. Add whatever is missing, then re-validate.

## Output
1. All node YAML files in `ballerina-graph/nodes/`, passing validation.
2. A short report in chat containing:
   - The final `validate` and `stats` output (node, item and edge counts)
   - A table: spec section → node id(s)
   - Spec sections you intentionally didn't cover, and why
   - Anything ambiguous, or anything you couldn't access or confirm in the 2024R1 spec