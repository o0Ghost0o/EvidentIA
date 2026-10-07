"""Graph service: persist relations and serve evidence trees.

Storage stays relational (``entities``/``relations`` tables); NetworkX builds
the in-memory neighbourhood for each tree query. Nodes: news, indicator,
event, entity. Edges: mentions, same_event, source_of, contradicts,
corroborates.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx
from sqlmodel import Session, select

from evidentia import models

logger = logging.getLogger(__name__)


def upsert_entity(session: Session, nombre: str, tipo: str, normalizado: str) -> models.Entity:
    entity = session.exec(
        select(models.Entity).where(models.Entity.normalizado == normalizado)
    ).first()
    if entity is None:
        entity = models.Entity(nombre=nombre, tipo=tipo, normalizado=normalizado)
        session.add(entity)
        session.flush()
    return entity


def add_relation(
    session: Session,
    origen_tipo: str, origen_id: str,
    destino_tipo: str, destino_id: str,
    tipo: str, peso: float = 1.0,
) -> models.Relation:
    existing = session.exec(
        select(models.Relation).where(
            models.Relation.origen_tipo == origen_tipo,
            models.Relation.origen_id == origen_id,
            models.Relation.destino_tipo == destino_tipo,
            models.Relation.destino_id == destino_id,
            models.Relation.tipo == tipo,
        )
    ).first()
    if existing is not None:
        return existing
    relation = models.Relation(
        origen_tipo=origen_tipo, origen_id=origen_id,
        destino_tipo=destino_tipo, destino_id=destino_id,
        tipo=tipo, peso=peso,
    )
    session.add(relation)
    return relation


def persist_graph(
    session: Session, articles: list[dict], relations: list[dict]
) -> dict[str, int]:
    """Persist enriched articles + relations; returns counts."""
    from evidentia.graph import entities as ent

    counts = {"entities": 0, "relations": 0}
    for article in articles:
        obj = session.exec(
            select(models.NewsArticle).where(
                models.NewsArticle.id_noticia == article["id_noticia"]
            )
        ).first()
        if obj is None:
            continue
        if article.get("agencia_primaria"):
            obj.agencia_primaria = article["agencia_primaria"]
            agency_norm = ent.normalize_entity(f"agency {article['agencia_primaria']}")
            agency = upsert_entity(
                session, article["agencia_primaria"], "AGENCY", agency_norm
            )
            counts["entities"] += 1
            # rewrite placeholder agency target to the real entity row id
            for rel in relations:
                if rel["tipo"] == "source_of" and rel["destino_id"] == f"agency:{article['agencia_primaria']}":
                    rel["destino_id"] = str(agency.id)
        if article.get("grupo_evento_id"):
            obj.grupo_evento_id = article["grupo_evento_id"]
        # entity mentions
        for name, tipo in ent.extract_entities(article.get("titulo") or ""):
            entity = upsert_entity(session, name, tipo, ent.normalize_entity(name))
            counts["entities"] += 1
            add_relation(
                session, "news", article["id_noticia"],
                "entity", str(entity.id), "mentions", 0.7,
            )
            counts["relations"] += 1
    for rel in relations:
        add_relation(session, **rel)
        counts["relations"] += 1
    session.commit()
    return counts


def _node_label(tipo: str, ref: str, session: Session) -> str:
    if tipo == "news":
        obj = session.exec(
            select(models.NewsArticle).where(models.NewsArticle.id_noticia == ref)
        ).first()
        return (obj.titulo if obj else ref) or ref
    if tipo == "entity":
        try:
            obj = session.get(models.Entity, int(ref))
        except (TypeError, ValueError):
            obj = None
        return (obj.nombre if obj else ref) or ref
    if tipo == "indicator":
        return ref
    if tipo == "event":
        obj = session.exec(
            select(models.GeoEvent).where(models.GeoEvent.event_id == ref)
        ).first()
        return (obj.place if obj and obj.place else ref) or ref
    return ref


def evidence_tree(
    session: Session, root_tipo: str, root_id: str, depth: int = 5
) -> dict[str, Any]:
    """Return the neighbourhood of a node as JSON-serializable nodes + edges."""
    graph = nx.DiGraph()
    for rel in session.exec(select(models.Relation)).all():
        src, dst = (rel.origen_tipo, rel.origen_id), (rel.destino_tipo, rel.destino_id)
        graph.add_edge(src, dst, tipo=rel.tipo, peso=rel.peso)

    root = (root_tipo, root_id)
    if root not in graph:
        graph.add_node(root)
    ego = nx.ego_graph(graph.to_undirected(), root, radius=depth)

    nodes = [
        {"tipo": tipo, "id": ref, "label": _node_label(tipo, ref, session)}
        for tipo, ref in ego.nodes
    ]
    edges = [
        {"origen_tipo": a[0], "origen_id": a[1], "destino_tipo": b[0], "destino_id": b[1],
         **ego.edges[a, b]}
        for a, b in ego.edges
    ]
    return {"root": {"tipo": root_tipo, "id": root_id}, "nodes": nodes, "edges": edges}


def count_primary_sources(session: Session, news_ids: list[str]) -> int:
    """Count independent provenances: one agency replica group = 1 source."""
    agencies: set[str] = set()
    independents = 0
    for nid in news_ids:
        obj = session.exec(
            select(models.NewsArticle).where(models.NewsArticle.id_noticia == nid)
        ).first()
        if obj is None:
            continue
        if obj.agencia_primaria:
            agencies.add(obj.agencia_primaria)
        else:
            independents += 1
    return len(agencies) + independents
