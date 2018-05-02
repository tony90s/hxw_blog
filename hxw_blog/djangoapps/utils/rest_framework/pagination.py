from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class LargeResultsSetPagination(PageNumberPagination):
    page_size = settings.PAGINATORS['LARGE_PAGE_SIZE']
    page_size_query_param = 'page_size'


class StandardResultsSetPagination(PageNumberPagination):
    page_size = settings.PAGINATORS['STANDARD_PAGE_SIZE']
    page_size_query_param = 'page_size'


class SmallResultsSetPagination(PageNumberPagination):
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']
    page_size_query_param = 'page_size'
