"""API endpoints for Modo Jurado: live execution and benchmark reporting."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from evidentia.jurado.service import (
    correr_pruebas_jurado,
    obtener_metricas_jurado,
    obtener_ultimo_jurado,
)

router = APIRouter(prefix="/jurado", tags=["jurado"])


@router.get("/pruebas", summary="Obtener el último informe de pruebas de aceptación T01–T10")
def get_pruebas() -> dict[str, Any]:
    """Retorna el resultado en caché o precalculado de la suite de aceptación oficial."""
    return obtener_ultimo_jurado()


@router.post("/pruebas", summary="Ejecutar en vivo la suite de aceptación T01–T10")
def post_correr_pruebas() -> dict[str, Any]:
    """Ejecuta en vivo pytest tests/test_acceptance.py y retorna el veredicto en tiempo real."""
    return correr_pruebas_jurado()


@router.get("/metricas", summary="Obtener comparativa de métricas del Agente vs Baseline BM25")
def get_metricas() -> dict[str, Any]:
    """Retorna la tabla comparativa de desempeño y evaluación del pliego oficial."""
    return obtener_metricas_jurado()
