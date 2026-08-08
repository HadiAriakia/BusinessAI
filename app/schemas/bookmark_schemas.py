from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

MAX_URL_LENGTH = 2048
MAX_TAG_LENGTH = 50
MAX_TAGS = 20


def normalise_tags(tags: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned:
            seen[cleaned] = None
    return list(seen)


class BookmarkCreate(BaseModel):
    url: HttpUrl = Field(examples=["https://example.com/article"])
    title: str = Field(min_length=1, max_length=200, examples=["Great Article"])
    description: str | None = Field(
        default=None, max_length=500, examples=["An insightful read on..."]
    )
    tags: list[str] = Field(
        default_factory=list, examples=[["python", "tutorial", "backend"]]
    )

    @field_validator("url")
    @classmethod
    def url_fits_the_column(cls, value: HttpUrl) -> HttpUrl:
        if len(str(value)) > MAX_URL_LENGTH:
            raise ValueError(f"URL must be at most {MAX_URL_LENGTH} characters")
        return value

    @field_validator("title")
    @classmethod
    def title_is_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        return cleaned

    @field_validator("description")
    @classmethod
    def blank_description_is_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        tags = normalise_tags(value)
        if len(tags) > MAX_TAGS:
            raise ValueError(f"at most {MAX_TAGS} tags")
        for tag in tags:
            if len(tag) > MAX_TAG_LENGTH:
                raise ValueError(f"tag must be at most {MAX_TAG_LENGTH} characters")
        return tags


class BookmarkUpdate(BaseModel):


    url: HttpUrl | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None

    _fit_url = field_validator("url")(BookmarkCreate.url_fits_the_column.__func__)
    _clean_title = field_validator("title")(BookmarkCreate.title_is_not_blank.__func__)
    _clean_description = field_validator("description")(
        BookmarkCreate.blank_description_is_null.__func__
    )
    _clean_tags = field_validator("tags")(BookmarkCreate.clean_tags.__func__)


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    title: str
    description: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def tag_names(cls, value):
        return [tag.name if hasattr(tag, "name") else tag for tag in value]
