from pydantic import BaseModel, Field


class PageMeta(BaseModel):
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Number of items requested per page")
    total_items: int = Field(description="Total number of items available across all pages")
    total_pages: int = Field(description="Total number of pages calculated from total_items / page_size")


class PageLink(BaseModel):
    next_page: str | None = Field(description="URL for the next page of results (null if on last page)")
    prev_page: str | None = Field(description="URL for the previous page of results (null if on first page)")
    actual_page: str = Field(description="URL of the current page being displayed")


class PageResult[T: BaseModel](BaseModel):
    items: list[T] = Field(description="Array of data items for the current page")
    links: PageLink = Field(description="Navigation links for pagination")
    meta: PageMeta = Field(description="Metadata about the pagination state")
