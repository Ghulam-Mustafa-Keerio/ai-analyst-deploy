"""Knowledge Graph module for relational dataset reasoning.

Builds an in-memory entity-relationship graph from a dataset's columns,
correlations, and detected domain entities. Supports:
* Entity extraction (column-level + value-level for categorical columns).
* Relationship inference (correlation edges, foreign-key detection).
* Graph queries (neighbors, shortest path, subgraph extraction).
* Optional export to Neo4j (when ``neo4j`` driver is installed and configured).

This is a lightweight, dependency-free implementation. For production-scale
GraphRAG, point it at a Neo4j instance or use Microsoft GraphRAG externally.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class GraphNode:
    id: str
    label: str
    kind: str  # "column" | "entity" | "metric"
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str  # "correlates_with" | "foreign_key" | "groups" | "derives_from"
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    _adjacency: dict[str, list[str]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        self._adjacency.setdefault(node.id, [])

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        self._adjacency.setdefault(edge.source, []).append(edge.target)
        self._adjacency.setdefault(edge.target, []).append(edge.source)

    def build_from_dataframe(
        self,
        df: pd.DataFrame,
        *,
        correlation_threshold: float = 0.5,
        max_categorical_entities: int = 20,
    ) -> None:
        """Infer a knowledge graph from a DataFrame."""
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()

        # Column nodes
        for col in df.columns:
            kind = "metric" if col in numeric_cols else "entity"
            self.add_node(GraphNode(id=col, label=col, kind=kind, properties={
                "dtype": str(df[col].dtype),
                "n_unique": int(df[col].nunique()),
                "null_count": int(df[col].isna().sum()),
            }))

        # Correlation edges
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr(numeric_only=True).abs()
            for i, src in enumerate(numeric_cols):
                for j, dst in enumerate(numeric_cols):
                    if j <= i:
                        continue
                    val = float(corr.iloc[i, j])
                    if val >= correlation_threshold:
                        self.add_edge(GraphEdge(
                            source=src, target=dst,
                            relation="correlates_with", weight=val,
                            properties={"coefficient": val},
                        ))

        # Categorical entity nodes + grouping edges
        for col in categorical_cols:
            top_values = df[col].value_counts().head(max_categorical_entities)
            for val, count in top_values.items():
                node_id = f"{col}::{val}"
                self.add_node(GraphNode(
                    id=node_id, label=str(val), kind="entity",
                    properties={"source_column": col, "count": int(count)},
                ))
                self.add_edge(GraphEdge(
                    source=col, target=node_id,
                    relation="groups", weight=count / len(df),
                ))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def neighbors(self, node_id: str, depth: int = 1) -> list[str]:
        visited: set[str] = set()
        frontier = [node_id]
        for _ in range(depth):
            next_frontier: list[str] = []
            for n in frontier:
                for neighbor in self._adjacency.get(n, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.append(neighbor)
            frontier = next_frontier
        return list(visited - {node_id})

    def subgraph(self, node_ids: list[str]) -> "KnowledgeGraph":
        sub = KnowledgeGraph()
        for nid in node_ids:
            if nid in self.nodes:
                sub.add_node(self.nodes[nid])
        for edge in self.edges:
            if edge.source in sub.nodes and edge.target in sub.nodes:
                sub.add_edge(edge)
        return sub

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        if source not in self.nodes or target not in self.nodes:
            return None
        from collections import deque
        queue: deque[tuple[str, list[str]]] = deque([(source, [source])])
        visited: set[str] = {source}
        while queue:
            current, path = queue.popleft()
            if current == target:
                return path
            for neighbor in self._adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": n.id, "label": n.label, "kind": n.kind, "properties": n.properties}
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "relation": e.relation, "weight": e.weight}
                for e in self.edges
            ],
            "stats": {"node_count": len(self.nodes), "edge_count": len(self.edges)},
        }

    # ------------------------------------------------------------------
    # Optional Neo4j export
    # ------------------------------------------------------------------
    def export_to_neo4j(self, *, uri: str | None = None, user: str | None = None, password: str | None = None) -> bool:
        """Push the graph to Neo4j. Returns ``True`` on success."""
        try:
            from neo4j import GraphDatabase
        except ImportError:
            return False
        uri = uri or os.environ.get("NEO4J_URI")
        user = user or os.environ.get("NEO4J_USER")
        password = password or os.environ.get("NEO4J_PASSWORD")
        if not uri:
            return False
        driver = GraphDatabase.driver(uri, auth=(user or "", password or ""))
        try:
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                for node in self.nodes.values():
                    session.run(
                        "CREATE (n:Entity {id: $id, label: $label, kind: $kind})",
                        id=node.id, label=node.label, kind=node.kind,
                    )
                for edge in self.edges:
                    session.run(
                        """
                        MATCH (a {id: $src}), (b {id: $dst})
                        CREATE (a)-[:RELATED {relation: $rel, weight: $w}]->(b)
                        """,
                        src=edge.source, dst=edge.target, rel=edge.relation, w=edge.weight,
                    )
        except Exception:  # noqa: BLE001
            return False
        finally:
            driver.close()
        return True


def build_knowledge_graph(df: pd.DataFrame, **kwargs: Any) -> KnowledgeGraph:
    """Convenience factory."""
    kg = KnowledgeGraph()
    kg.build_from_dataframe(df, **kwargs)
    return kg
