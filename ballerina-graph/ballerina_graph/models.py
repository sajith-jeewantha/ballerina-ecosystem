"""Pydantic models for the Ballerina Knowledge Graph (schema v0.1).

These models are the source of truth for the node file format.
`schema/node.schema.json` is generated from them; never edit it by hand.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "0.1"

NodeType = Literal["concept", "library", "tool", "topic"]
Priority = Literal["core", "important", "long_tail"]
Status = Literal["draft", "in_review", "approved", "deprecated"]
Difficulty = Literal["beginner", "intermediate", "advanced"]
SourceKind = Literal["spec", "bbe", "central", "docs", "github", "other"]
Relation = Literal[
    "requires", "implements", "uses", "part_of",
    "counterpart_of", "alternative_to", "related",
]

DIRECTED_RELATIONS: frozenset[str] = frozenset({"requires", "implements", "uses", "part_of"})
SYMMETRIC_RELATIONS: frozenset[str] = frozenset({"counterpart_of", "alternative_to", "related"})

ID_PREFIX: dict[str, str] = {
    "concept": "concept",
    "library": "lib",
    "tool": "tool",
    "topic": "topic",
}

NODE_ID_PATTERN = r"^(concept|lib|tool|topic)(\.[a-z0-9_]+)+$"
ITEM_ID_PATTERN = r"^[a-z0-9_]+(\.[a-z0-9_]+)*$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(_Strict):
    url: str = Field(description="Link to the spec section, Ballerina by Example page, Central docs, etc.")
    kind: SourceKind = "other"
    note: Optional[str] = None


class Item(_Strict):
    id: str = Field(pattern=ITEM_ID_PATTERN, description="Unique within the node.")
    text: str = Field(min_length=1, description="What must be covered, written as a concrete capability.")
    difficulty: list[Difficulty] = Field(
        default_factory=lambda: ["beginner", "intermediate", "advanced"]
    )
    sources: list[Source] = Field(default_factory=list)
    replaced_by: Optional[str] = Field(
        default=None, description="Item id in the same node that supersedes this one."
    )


class Edge(_Strict):
    to: str = Field(pattern=NODE_ID_PATTERN, description="Target node id.")
    rel: Relation
    via: list[str] = Field(default_factory=list, description="Item ids on the source node.")
    target_items: list[str] = Field(default_factory=list, description="Item ids on the target node.")
    note: Optional[str] = None


class Node(_Strict):
    schema_version: str = Field(description="Schema version the file was written against.")
    id: str = Field(pattern=NODE_ID_PATTERN)
    type: NodeType
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    priority: Priority = "important"
    status: Status = "draft"
    modules: list[str] = Field(default_factory=list, description="Ballerina modules, e.g. ballerina/http.")
    must_cover: list[Item] = Field(min_length=1)
    out_of_scope: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    replaced_by: Optional[str] = None
    notes: Optional[str] = Field(default=None, description="For reviewers; never sent to the generator.")

    @model_validator(mode="after")
    def _node_level_checks(self) -> "Node":
        prefix = ID_PREFIX[self.type]
        if not self.id.startswith(prefix + "."):
            raise ValueError(f"id '{self.id}' must start with '{prefix}.' for type '{self.type}'")
        if self.type == "library" and not self.modules:
            raise ValueError("library nodes must list at least one module")
        seen: set[str] = set()
        for item in self.must_cover:
            if item.id in seen:
                raise ValueError(f"duplicate item id '{item.id}'")
            seen.add(item.id)
        if self.status == "deprecated" and not self.replaced_by:
            raise ValueError("deprecated nodes must set replaced_by")
        for item in self.must_cover:
            if item.replaced_by and item.replaced_by not in seen:
                raise ValueError(f"item '{item.id}' replaced_by unknown item '{item.replaced_by}'")
        return self

    def item(self, item_id: str) -> Item:
        for it in self.must_cover:
            if it.id == item_id:
                return it
        raise KeyError(f"{self.id}#{item_id}")

    @property
    def item_ids(self) -> list[str]:
        return [it.id for it in self.must_cover]
