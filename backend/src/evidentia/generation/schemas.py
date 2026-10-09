"""Pydantic schemas for structured generation and frontend contract enforcement.

Ensures LLM responses adhere strictly to the expected editorial structure,
eliminating free-form leakage and guaranteeing strong typing for the UI.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class SentenceItemSchema(BaseModel):
    key: str = Field(default="", description="Identificador único de la oración (ej: brief-0)")
    section: str = Field(default="", description="Sección de origen: brief, guion, copy_digital, resumen, evidencia")
    text: str = Field(description="Texto limpio de la oración redactado en español")
    raw: str = Field(default="", description="Texto original de la oración")
    clase: Literal["hecho", "declaración", "inferencia", "hipótesis"] = Field(
        default="hecho",
        description="Clasificación epistémica: hecho, declaración, inferencia o hipótesis",
    )
    cls: Literal["hecho", "declaración", "inferencia", "hipótesis"] = Field(
        default="hecho",
        description="Alias de clase para consumo directo en el frontend",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Lista de citas válidas asociadas [id:campo]",
    )
    cite: str = Field(default="", description="Primera cita principal o cadena vacía")
    sin_respaldo: bool = Field(default=True, description="True si la afirmación carece de citas válidas")
    support_status: str = Field(default="sin respaldo", description="'respaldado' o 'sin respaldo'")
    has_support: bool = Field(default=False, description="True si cuenta con respaldo de fuentes")


class TvnBriefSchema(BaseModel):
    titulo_propuesto: str = Field(default="", description="Título periodístico propuesto en una línea")
    brief: str = Field(default="", description="Brief informativo de máximo 250 palabras en español")
    enfoque: str = Field(default="", description="Enfoque de interés público (2-3 líneas)")
    preguntas: list[str] | str = Field(default_factory=list, description="Preguntas de investigación")
    fuentes_y_verificaciones: list[str] | str = Field(default_factory=list, description="Fuentes y verificaciones pendientes con citas")
    guion: str = Field(default="", description="Guion locutable de 45-60 segundos")
    copy_digital: str = Field(default="", description="Texto para redes sociales de máximo 80 palabras")
    sentences: list[SentenceItemSchema] = Field(
        default_factory=list,
        description="Desglose clasificado por oración del brief y guion",
    )


class BancaBulletinSchema(BaseModel):
    resumen: str = Field(default="", description="Resumen de entorno de máximo 250 palabras en español")
    sectores: list[str] | str = Field(default_factory=list, description="Sectores económicos potencialmente relacionados")
    horizonte: str = Field(default="", description="Horizonte temporal justificado")
    evidencia: list[str] | str = Field(default_factory=list, description="Evidencias con separación de observación e hipótesis")
    preguntas: list[str] | str = Field(default_factory=list, description="Preguntas para el analista")
    sentences: list[SentenceItemSchema] = Field(
        default_factory=list,
        description="Desglose clasificado por oración del resumen y evidencia",
    )
