"""Parent/child chunk builders for news texts and indicator rows."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from evidentia.config import get_settings

INDICATOR_NAMES = {
    "NY.GDP.MKTP.KD.ZG": "Crecimiento del PIB",
    "FP.CPI.TOTL.ZG": "Inflación",
    "SL.UEM.TOTL.ZS": "Desempleo",
    "SP.POP.TOTL": "Población",
    "IT.NET.USER.ZS": "Uso de internet",
    "NE.EXP.GNFS.ZS": "Exportaciones/PIB",
}

COUNTRY_NAMES = {
    "PAN": "Panamá", "CRI": "Costa Rica", "COL": "Colombia",
    "DOM": "Rep. Dominicana", "MEX": "México", "GTM": "Guatemala",
}


def _splitter() -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.ingestion_chunk_size,
        chunk_overlap=settings.ingestion_chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def news_parent_id(id_noticia: str) -> str:
    return f"news:{id_noticia}"


def indicator_parent_id(pais_iso3: str, indicador_id: str, anio: int) -> str:
    return f"indicator:{pais_iso3}:{indicador_id}:{anio}"


def build_news_parent(row: dict) -> Document:
    """Build the parent document for a news row (title + available text)."""
    settings = get_settings()
    titulo = row.get("titulo") or ""
    # alcance_texto governs honesty downstream: only titles/metadata exist.
    text = titulo[: settings.ingestion_parent_size]
    return Document(
        page_content=text,
        metadata={
            "parent_id": news_parent_id(row["id_noticia"]),
            "root_id": row["id_noticia"],
            "tipo": "news",
            "id_noticia": row["id_noticia"],
            "titulo": titulo,
            "url": row.get("url") or "",
            "medio": row.get("medio") or "",
            "fecha_publicacion": str(row.get("fecha_publicacion") or ""),
            "tema": row.get("tema") or "",
            "origen": row.get("origen") or "",
            "alcance_texto": row.get("alcance_texto") or "titular",
            "agencia_primaria": row.get("agencia_primaria") or "",
        },
    )


def build_indicator_parent(row: dict) -> Document:
    """Render an indicator observation as a self-describing passage."""
    pais = COUNTRY_NAMES.get(row.get("pais_iso3") or "", row.get("pais_iso3") or "")
    nombre = INDICATOR_NAMES.get(row.get("indicador_id") or "", row.get("indicador_id") or "")
    anio = row.get("anio")
    valor = row.get("valor")
    unidad = row.get("unidad") or ""
    if valor is None:
        text = f"{pais} · {nombre} ({anio}): sin dato publicado. Fuente: Banco Mundial."
    else:
        text = f"{pais} · {nombre} ({anio}): {valor} {unidad}. Fuente: Banco Mundial."
    return Document(
        page_content=text,
        metadata={
            "parent_id": indicator_parent_id(row["pais_iso3"], row["indicador_id"], int(anio)),
            "root_id": f"{row['pais_iso3']}:{row['indicador_id']}:{anio}",
            "tipo": "indicator",
            "pais_iso3": row.get("pais_iso3") or "",
            "indicador_id": row.get("indicador_id") or "",
            "anio": anio,
            "valor": valor,
            "unidad": unidad,
            "fuente_url": row.get("fuente_url") or "",
        },
    )


def split_children(parent: Document) -> list[Document]:
    """Split a parent into child chunks carrying the parent link + trace fields."""
    splitter = _splitter()
    children = splitter.split_documents([parent])
    for child in children:
        child.metadata["doc_id"] = parent.metadata["parent_id"]
    return children
