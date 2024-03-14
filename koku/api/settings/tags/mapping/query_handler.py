#
# Copyright 2024 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""Query handler for Tag Mappings."""
import dataclasses
import uuid
@dataclasses.dataclass(frozen=True)
class TagKey:
    uuid: str
    key: uuid.UUID
    source_type: str


@dataclasses.dataclass
class Relationship:
    parent: TagKey
    child: TagKey = None
    children: list[TagKey] = dataclasses.field(default_factory=list)

    @classmethod
    def create_from_data(cls, data: list[dict[str: dict[str: uuid.UUID | str]]]):
        return [
            cls(
                parent=TagKey(**item["parent"]),
                child=TagKey(**item["child"]),
            )
            for item in data
        ]

    @property
    def all_children(self):
        return [self.child, *self.children]


def format_tag_mapping_relationship(relationships: list[Relationship]) -> list[dict[str: uuid.UUID | str]]:
    formatted_relationships = {}
    for relationship in relationships:
        parent_uuid = relationship.parent.uuid
        if parent_uuid not in formatted_relationships:
            formatted_relationships[parent_uuid] = Relationship(
                parent=relationship.parent,
                # child=relationship.child,
                children=relationship.all_children,  # ?
            )
        else:
            formatted_relationships[parent_uuid].children.extend(relationship.all_children)

    return [dataclasses.asdict(relationship) for relationship in formatted_relationships.values()]
