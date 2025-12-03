from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинатор PageNumberPagination с ограничением страниц через limit."""

    page_size_query_param = 'limit'
    page_size = 6
