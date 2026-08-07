from pydantic import BaseModel, Field


class TagCount(BaseModel):
    name: str = Field(examples=["python"])
    count: int = Field(examples=[45])


class MonthCount(BaseModel):
    month: str = Field(examples=["2026-01"], description="YYYY-MM")
    count: int = Field(examples=[23])


class StatsResponse(BaseModel):
    """Aggregates over the authenticated user's bookmarks only."""

    total_bookmarks: int
    total_tags: int = Field(description="Distinct tags used across your bookmarks.")
    top_tags: list[TagCount] = Field(description="Most used first, up to ten.")
    bookmarks_per_month: list[MonthCount] = Field(description="Oldest month first.")
