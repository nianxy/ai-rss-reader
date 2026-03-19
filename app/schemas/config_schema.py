from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    name: str
    url: str
    icon: str = ''
    fetch_limit: int = Field(default=20, ge=1, le=200)


class CategoryConfig(BaseModel):
    id: str
    name: str
    sources: list[SourceConfig]


class RSSConfig(BaseModel):
    categories: list[CategoryConfig]
