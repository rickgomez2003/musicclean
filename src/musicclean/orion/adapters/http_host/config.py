"""Configuration for the Orion HTTP host."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HttpHostConfig:
    title: str = "MusicClean Orion API"
    version: str = "0.6.20"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
