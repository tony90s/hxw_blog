"""
URLs for API
"""
from django.conf.urls import url, include

urlpatterns = [
    url(r'^account/', include('restful_api.account.urls')),
    url(r'^article/', include('restful_api.article.urls')),
]
