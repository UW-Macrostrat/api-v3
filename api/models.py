import os
from typing import Optional

from geojson_pydantic import Feature, Polygon
from pydantic import BaseModel, ConfigDict, field_validator


class CommonModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_id: Optional[int] = None
    orig_id: Optional[int] = None
    descrip: Optional[str] = None
    ready: Optional[bool] = None

    @field_validator("source_id", "orig_id")
    def transform_str_to_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v


class PolygonModel(CommonModel):
    name: Optional[str] = None
    strat_name: Optional[str] = None
    age: Optional[str] = None
    comments: Optional[str] = None
    t_interval: Optional[int] = None
    b_interval: Optional[int] = None
    geom: Optional[Polygon] = None

    @field_validator("t_interval", "b_interval")
    def transform_str_to_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v


class LineworkModel(CommonModel):
    name: Optional[str] = None
    type: Optional[str] = None
    direction: Optional[str] = None

class CopyColumnRequest(BaseModel):
    source_column: str

# Database Models

class Sources(BaseModel):
    source_id: int
    name: Optional[str] = None
    primary_table: str
    url: Optional[str] = None
    ref_title: Optional[str] = None
    authors: Optional[str] = None
    ref_year: Optional[str] = None
    ref_source: Optional[str] = None
    isbn_doi: Optional[str] = None
    scale: Optional[str] = None
    primary_line_table: Optional[str] = None
    licence: Optional[str] = None
    features: Optional[int] = None
    area: Optional[int] = None
    priority: bool
    rgeom: Optional[Polygon] = None
    display_scales: Optional[list[str]] = None
    web_geom: Optional[Polygon] = None
    new_priority: int
    status_code: str

    class Config:
        orm_mode = True



