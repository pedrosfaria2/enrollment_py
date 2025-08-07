from typing import Any
from urllib.parse import parse_qsl, urlencode

from fastapi import Request
from loguru import logger
from pydantic import BaseModel

from infra.schemas.pagination import PageLink, PageMeta, PageResult


class Pagination[T: BaseModel]:
    """
    Class for creating pagination objects in API responses.

    This class allows generating a consistent pagination structure to be used in API responses,
    supporting both database-level pagination and code-level pagination.

    Parameters:
    - request (Request): FastAPI request object.
    - items (List[Any]): List of items to be included in the current page.
    - page (int): Current page number.
    - page_size (int): Number of items per page.
    - schema_class (Type[T]): Pydantic class used to serialize the items.
    - total_items (Optional[int]): Total available items. If not provided, will be calculated based on the `items` list size.
    - paginate_in_code (bool): Indicates whether pagination should be performed in code (True) or if items are already paginated (False).

    Operation:

    Database Pagination (paginate_in_code=False):
    When pagination is performed directly in the database query, the items provided in `items`
    already correspond to the requested page. In this case, it's necessary to inform the total available items in `total_items`
    so that the `total_pages` calculation is correct. The class uses `total_items` to generate pagination metadata and links.

    Code Pagination (paginate_in_code=True):
    When all items are retrieved from the database without pagination, the class performs pagination in code.
    Items are sliced internally based on the `page` and `page_size` parameters. The total items is calculated
    automatically using `len(items)`, if `total_items` is not provided.


    Usage Examples:

    Database Pagination:
    total_items = use_case.count_all(db)
    offset = (page - 1) * page_size
    limit = page_size
    items = use_case.get_all(db, offset=offset, limit=limit)
    result = Pagination[ItemSchema].create(
        request=request,
        items=items,
        total_items=total_items,
        page=page,
        page_size=page_size,
        schema_class=ItemSchema,
    )

    Code Pagination:
    items = use_case.get_all(db)
    result = Pagination[ItemSchema].create(
        request=request,
        items=items,
        page=page,
        page_size=page_size,
        schema_class=ItemSchema,
        paginate_in_code=True,
    )

    Note:
    The choice between database or code pagination depends on the context and application performance needs.
    For large datasets, it's recommended to perform pagination at the database level to reduce memory consumption
    and processing time. The Pagination class was designed to accommodate both approaches transparently.
    """

    @classmethod
    def create(
        cls,
        *,
        request: Request,
        items: list[Any],
        page: int,
        page_size: int,
        schema_class: type[T],
        total_items: int | None = None,
        paginate_in_code: bool = False,
    ) -> PageResult[T]:
        if total_items is None:
            logger.debug("total_items should be provided for accurate pagination.")
            total_items = len(items)

        total_pages = max(1, (total_items + page_size - 1) // page_size)

        if page > total_pages:
            paginated_items = []
        elif paginate_in_code:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_items = items[start_index:end_index]
        else:
            paginated_items = items

        pydantic_items = [schema_class.model_validate(item) for item in paginated_items]

        actual_page = str(request.url)
        base_url, _, query_string = actual_page.partition("?")
        existing_params = dict(parse_qsl(query_string))
        existing_params["page_size"] = str(page_size)

        def build_url(new_page: int) -> str:
            params = existing_params.copy()
            params["page"] = str(new_page)
            return f"{base_url}?{urlencode(params)}"

        next_page = build_url(page + 1) if page < total_pages else None
        prev_page = build_url(page - 1) if page > 1 else None

        return PageResult[T](
            items=pydantic_items,
            meta=PageMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
            links=PageLink(
                next_page=next_page,
                prev_page=prev_page,
                actual_page=actual_page,
            ),
        )
