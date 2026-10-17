from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChangeRequestCreate(BaseModel):
    project_id: UUID
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ChangeRequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=40)

    model_config = ConfigDict(str_strip_whitespace=True)


class ChangeRequestRead(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
