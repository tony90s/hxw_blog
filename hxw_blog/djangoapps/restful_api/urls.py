"""
URLs for API
"""
from django.conf.urls import url, include

urlpatterns = [
    url(r'^', include('restful_api.article.urls')),
]
