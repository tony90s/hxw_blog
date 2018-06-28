"""microsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os

from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from microsite_index.views import index_view, search_view

urlpatterns = [
    url(r'^$', index_view, name='index'),
    url(r'^search$', search_view, name='search'),
    url(r'^account/', include('microsite_account.urls', namespace='account')),
    url(r'^article/', include('microsite_article.urls', namespace='article')),
    url(r'^api/v1/', include('api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/upload/', document_root=os.path.join(settings.ENV_ROOT, "upload"))
    urlpatterns += static('/downloads/', document_root=os.path.join(settings.ENV_ROOT, "downloads"))
