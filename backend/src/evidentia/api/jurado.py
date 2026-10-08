"""API endpoints for Modo Jurado: live execution and benchmark reporting in Markdown & JSON."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Response

from evidentia.jurado.service import (
    correr_pruebas_jurado,
    obtener_metricas_jurado,
    obtener_reporte_markdown,
    obtener_ultimo_jurado,
)

router = APIRouter(prefix="/jurado", tags=["jurado"])


@router.get("/pruebas", summary="Obtener el último informe de pruebas de aceptación T01–T10")
def get_pruebas() -> dict[str, Any]:
    """Retorna el resultado de la suite de aceptación oficial en JSON con Markdown estructurado incluido."""
    return obtener_ultimo_jurado()


@router.post("/pruebas", summary="Ejecutar en vivo la suite de aceptación T01–T10")
def post_correr_pruebas() -> dict[str, Any]:
    """Ejecuta en vivo T01–T10 sin dependencias XML y retorna el informe en JSON con Markdown estructurado."""
    return correr_pruebas_jurado()


@router.get("/reporte", summary="Obtener el reporte oficial de aceptación en formato Markdown o JSON")
def get_reporte(formato: str = Query("markdown", description="Formato del reporte ('markdown' o 'json')")) -> Any:
    """Retorna el reporte de aceptación en el formato solicitado (Markdown por defecto)."""
    if formato.lower() == "json":
        return obtener_ultimo_jurado()
    md_content = obtener_reporte_markdown()
    return Response(
        content=md_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'inline; filename="reporte_jurado_evidentia.md"'},
    )


@router.get("/reporte.md", summary="Descargar el reporte oficial de aceptación como archivo Markdown (.md)")
def get_reporte_archivo_md() -> Response:
    """Descarga directa del reporte de jurado en formato Markdown (.md)."""
    md_content = obtener_reporte_markdown()
    return Response(
        content=md_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reporte_jurado_evidentia.md"'},
    )


@router.get("/metricas", summary="Obtener comparativa de métricas del Agente vs Baseline BM25")
def get_metricas() -> dict[str, Any]:
    """Retorna la tabla comparativa de desempeño y evaluación del pliego oficial."""
    return obtener_metricas_jurado()
